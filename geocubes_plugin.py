# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeocubesPlugin
                                 A QGIS plugin
 Interface to download raster data from GeoCubes Finland
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-06-04
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Paikkatietokeskus FGI
        email                : lassi.lehto@nls.fi
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QTableWidgetItem, QAbstractScrollArea
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsRasterLayer,
                       QgsMessageLog, Qgis)
from qgis.gui import QgsBusyIndicatorDialog

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .geocubes_plugin_dialog import GeocubesPluginDialog
import os.path, requests


class GeocubesPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeocubesPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GeoCubes Plugin')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeocubesPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/geocubes_plugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Download harmonised raster data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GeoCubes Plugin'),
                action)
            self.iface.removeToolBarIcon(action)

    def setResolution(self):
        """Resolution is set to be the one currently in the box"""
        self.resolution = self.resolution_box.currentText()
        
            
    def getDatasets(self):
        """Sends a query to Geocubes and receives text describing the data.
           Returns a list of strings containing the datasets"""
        
        # request info from the server: if no response in 10 seconds, timeout
        response = requests.get(self.url_base + "/info/getDatasets", timeout=10)
        
        # request status code indicates whether succesful: if not, raise an exception
        if (response.status_code >= 500):
            raise Exception('Server timed out')

        # decode from bytes to string
        response_string = response.content.decode("utf-8")

        # datasets are divided by semicolons: split at semicolons
        dataset_list = response_string.split(';')

        return dataset_list

    def setToTable(self):
        """
        Activated when user clicks "Fetch datasets" button. This function
        lists available data to the user and creates checkboxes that allow
        the selection of said data. Also creates signals that cannot be
        created on first start, like the signal emitted when clicking 
        on a checkbox.
        """
        # if previous signals exist, i.e. the plugin is started multiple times,
        # remove the connections. If none exist, pass
        try: self.table.itemChanged.disconnect() 
        except Exception: pass

        # get a list of datasets
        datasets = self.getDatasets()

        self.table.setColumnCount(4)
        # start with only 1 row, add more as needed
        self.table.setRowCount(1)
        # set headers for all 4 columns
        self.table.setHorizontalHeaderLabels(['Label', 'Year', 'Maxres (m)', 'Select'])

        # loop through all the datasets
        for i, dataset in enumerate(datasets):
            # entries in the datasets are separated by commas
            dataset_split = dataset.split(',')

            # each entry has seven pieces of info, but only four are needed

            # label = a plain language name for the dataset: can have spaces etc.
            label = dataset_split[0]

            # name = version of label used in queries etc.
            name = dataset_split[1]
            years = dataset_split[2]
            # maxres = maximum resolution of the dataset in meters
            maxres = dataset_split[5]

            # years are separated by periods
            years_split = years.split('.')
            
            # one dataset may have data from multiple years
            # this is handled by adding each year on its own row
            for year in years_split:
                # the strings must be transformed to Qt Items
                label_entry = QTableWidgetItem(label)
                # the items must NOT be selectable or otherwise modifiable
                label_entry.setFlags(Qt.NoItemFlags)
                maxres_entry = QTableWidgetItem(maxres)
                maxres_entry.setFlags(Qt.NoItemFlags)
                year_entry = QTableWidgetItem(year)
                year_entry.setFlags(Qt.NoItemFlags)
                
                # create a checkbox for each row
                checkbox_entry = QTableWidgetItem()
                checkbox_entry.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                # start with checkbox unchecked
                checkbox_entry.setCheckState(Qt.Unchecked)
                
                # get the current row count from the table
                row_count = self.table.rowCount()
                
                """Next, add info of the dataset to our dictionary. The dict
                will later be accessed via the list of downloadable datasets:
                it will house the keys. This way may seem redundant, but it's done
                since the name variable isn't needed on the table but is later
                necessary for the queries"""
                key = label + ";" + year
                value = name + ";"+ year
                
                self.datasets_all[key] = value

                
                # add the previously created items on the table
                self.table.setItem(row_count-1, 0, label_entry)
                self.table.setItem(row_count-1, 1, year_entry)
                self.table.setItem(row_count-1, 2, maxres_entry)
                self.table.setItem(row_count-1, 3, checkbox_entry)
                
                # if there're datasets left, add a new row
                if i < len(datasets)-1:
                    self.table.setRowCount(row_count+1)
        
        # fit column sizes to the items
        self.table.resizeColumnsToContents()
        
        # when an item's content are changed, or in this case, when a checkbox
        # is checked or unchecked, run the function
        self.table.itemChanged.connect(self.checkboxState)
        
        # add or subtract from the layer count
        self.table.itemChanged.connect(self.updateCountText)
        
    def updateCountText(self):
        """Activated when checkbox states change. Updates the count accordingly"""
        if len(self.datasets_to_download) == 1:
            self.layer_count_text.setText(str(len(self.datasets_to_download))+
                                          ' layer selected')
        else:
            self.layer_count_text.setText(str(len(self.datasets_to_download))+
                                          ' layers selected')
            
    def updateDataText(self, msg):
        self.data_info_text.setText(msg)
            
    def checkboxState(self, cbox):
        """itemChanged signal passes the checkbox (cbox). This function
           checks whether cbox was checked or unchecked and acts accordingly"""
        state = cbox.checkState()
        
        # 0 = unchecked, 2 = checked
        if state == 0:
            self.stateNegative(cbox)
        elif state == 2:
            self.statePositive(cbox)

    def stateNegative(self, cbox):
        """This function is called in case the cbox is unchecked.
           Removes the dataset in question from the list"""
           
        # cbox has a function to access its row number in the table
        # this is used to access label and year items,
        # since they're on the same row and their column number are known
        box_row = cbox.row()
        label_item = self.table.item(box_row, 0)
        label_text = label_item.text()
        
        year_item = self.table.item(box_row, 1)
        year_text = year_item.text()
        
        # create key in the same format as before
        dataset_key = label_text + ";" + year_text
        
        # if key already exists, remove it
        if dataset_key in self.datasets_to_download:
            self.datasets_to_download.remove(dataset_key)
    
    def statePositive(self, cbox):
        """This function is called in case the cbox is checked.
           Adds the dataset in question from the list. See above for details"""
        box_row = cbox.row()
        label_item = self.table.item(box_row, 0)
        label_text = label_item.text()

        year_item = self.table.item(box_row, 1)
        year_text = year_item.text()

        dataset_key = label_text + ";" + year_text
        self.datasets_to_download.append(dataset_key)

    def deleteDownloads(self):
        """Called when datasets are fetched more than once, which empties the list.
           Also updates layer count"""
        self.datasets_to_download.clear()
        self.updateCountText()
        
    def getValues(self):
        """Extracts all values (name/year pairs separated by a semicolon)
            Returns them as a list"""
        values = []
        
        for dataset_key in self.datasets_to_download:
            # get value by passing the key from the download list
            value = self.datasets_all[dataset_key]
            values.append(value)
            
        return values
            
    def getData(self):
        """
        Downloads raster datasets from Geocubes servers as selected by the user
        This is done by forming an url comprised of layer names, years, extent
        and resolution. Either directly creates a QGis raster layer by 
        passing the url as data source (referred to as temp layer, though strictly
        speaking I don't believe it's saved to some temp folder. Not sure though).
        Another option is to save layers to disk and passing that as the source.
        [SAVE TO DISK TO BE IMPLEMENTED]
        """
        # nothing will be downloaded if nothing is selected. Notifies user. Else continue
        if(len(self.datasets_to_download) == 0):
            self.updateDataText("Please select one or more layers!")
        else:
            # get info that's passed to the Geocubes server
            dataset_parameters = self.getValues()
            extent = self.getExtent()
            
            # this is needed to form a while loop
            done = False
            
            # while datasets are downloaded, an indicator will be shown
            busy_dialog = QgsBusyIndicatorDialog("Fetching data...", self.dlg)
            busy_dialog.show()
            
            # a simple count of succesful downloads
            successful_layers = 0
        
            while not done:
                # 1 to n loops to download all selected data
                for parameter in dataset_parameters:
                    # name and year are stored as a string and separeted by ';'
                    name_and_year = parameter.split(';')
                    
                    # forming the url that's passed to server
                    # see http://86.50.168.160/geocubes/examples/ 
                    # for examples of forming this url
                    data_url = (self.url_base + "/clip/" + self.resolution +
                        "/"+name_and_year[0]+"/bbox:" + self.formatExtent(extent)
                        + "/" + name_and_year[1])
                    
                    # creating raster layer by passing the url and giving
                    # paramter (name;year) as layer name
                    raster_layer = QgsRasterLayer(data_url, parameter)
                    
                    # if data query fails, inform user. If not, add to Qgis
                    if not raster_layer.isValid():
                        self.iface.messageBar().pushMessage("Layer invalid", 
                                        parameter+" failed to download", level=Qgis.Warning,
                                        duration = 9)
                    else:
                        QgsProject.instance().addMapLayer(raster_layer)
                        successful_layers += 1
                
                # once all layers are downloaded, inform how many were succesful
                self.updateDataText(str(successful_layers) + "/" +
                                    str(len(dataset_parameters))+ " layer(s)" +
                                    " successfully downloaded")
                busy_dialog.close()
                done = True
            
        
            
    def getExtent(self):
        """Current extent shown in the extent groupbox
        Returns a rectangle object"""
        output_extent = self.extent_box.outputExtent()
        return output_extent
        """
        
        QgsMessageLog.logMessage(output_extent,
                                 'geocubes_plugin',
                                 Qgis.Info)
        """
        
    def formatExtent(self,rectangle):
        """The extent coordinates need to be in certain format for the url
            This function's input is a Qgis rectangle and output a bbox string"""
        formatted_extent = (str(rectangle.xMinimum())+','+str(rectangle.yMinimum())
                            +','+str(rectangle.xMaximum())+','+str(rectangle.yMaximum()))
        return formatted_extent           

    def run(self):
        """Run method that performs all the real work"""

        # if the plugin is started for the first time,
        # create necessary variables and connect signals to slots
        # signal/slot connection must only be made once;
        # unless disconnected elsewhere
        if self.first_start is True:
            self.first_start = False
            # the ui
            self.dlg = GeocubesPluginDialog()
            
            # current base url of the Geocubes project. Modify if url changes
            self.url_base = "http://86.50.168.160/geocubes"
            
            # table to house the datasets: also add policies to fit the data
            # better on the table
            self.table = self.dlg.tableWidget
            self.table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            
            # connect click of the fetch data layers button to functions
            self.dlg.getContents.clicked.connect(self.setToTable)
            self.dlg.getContents.clicked.connect(self.deleteDownloads)
            
            self.extent_box = self.dlg.mExtentGroupBox
            
            # box housing a drop-down list of possible raster resolutions
            self.resolution_box = self.dlg.resolutionBox
            self.resolution_box.activated.connect(self.setResolution)
            
            self.data_button = self.dlg.getDataButton
            self.data_button.clicked.connect(self.getData)
            
            # text that tells the user the current count of selected layers
            self.layer_count_text = self.dlg.layerCountText
            
            # text that informs the user on things related to downloading
            # the data layers
            self.data_info_text = self.dlg.dataInfoText
            
            # radio buttons for user to decide whether to get the data as
            # temporary layers or save the rasters to disc
            self.save_temp_button = self.dlg.saveToTempButton
            
            # QGIS canvas
            self.canvas = self.iface.mapCanvas()
        
        # list of possible resolutions. Update if this changes
        resolutions = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        # empty the box when plugin is restarted
        self.resolution_box.clear()
        self.resolution_box.addItems(str(resolution) for resolution in resolutions)
        # set '100' as the default selection
        self.resolution_box.setCurrentIndex(6)
        
        # this variable houses the currently selected resolution
        self.resolution = self.resolution_box.currentText()
        
        # an empty dictionary to house all the fetched datasets
        self.datasets_all = {}
        
        # an empty list for only the datasets the user has selected
        self.datasets_to_download = []
        
        # initialising the extent box
        # all the data is in ETRS89 / TM35FIN (EPSG:3067), 
        # therefore that's the default crs
        proj_crs = QgsCoordinateReferenceSystem('EPSG:3067')
        # current extent, or bounding box
        og_extent = self.canvas.extent()

        # these three things must be set when initialising the extent box
        self.extent_box.setOriginalExtent(og_extent, self.canvas.mapSettings().destinationCrs())
        self.extent_box.setCurrentExtent(og_extent, proj_crs)
        self.extent_box.setOutputCrs(proj_crs)
        
        # set default texts
        self.layer_count_text.setText('0 layers selected')
        self.data_info_text.setText('Get datasets here')
        
        self.save_temp_button.setChecked(True)
        
        # make sure the table is empty on restart
        self.table.clear()
        
        # show the dialog
        self.dlg.show()
        
        # Run the dialog event loop
        """
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
        """
