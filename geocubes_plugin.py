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
from PyQt5.QtWidgets import QAction, QTableWidgetItem, QCheckBox, QAbstractScrollArea
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem, QgsRasterLayer,
                       QgsMessageLog, Qgis)

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
        self.resolution = self.resolution_box.currentText()
            
    def getDatasets(self):
        response = requests.get(self.url_base + "/info/getDatasets", timeout=10)

        if (response.status_code >= 500):
            raise Exception('Server timed out')
            
        response_string = response.content.decode("utf-8")

        # datasets are divided by semicolons: split at them
        dataset_list = response_string.split(';')
        
        return dataset_list
    
    def setToTable(self):
        datasets = self.getDatasets()
        
        self.table.setColumnCount(4)
        self.table.setRowCount(1)
        self.table.setHorizontalHeaderLabels(['Label', 'Year', 'Maxres (m)', 'Select'])
        
        for i, dataset in enumerate(datasets):
            # entries in the datasets are separated by commas
            dataset_split = dataset.split(',')
            name = dataset_split[0]
            years = dataset_split[2]
            maxres = dataset_split[5]
            
            years_split = years.split('.')
            
            for year in years_split:
                name_entry = QTableWidgetItem(name)
                name_entry.setFlags(Qt.NoItemFlags)
                maxres_entry = QTableWidgetItem(maxres)
                maxres_entry.setFlags(Qt.NoItemFlags)
                checkbox_entry = QTableWidgetItem()
                checkbox_entry.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                checkbox_entry.setCheckState(Qt.Unchecked)
                
                row_count = self.table.rowCount()

                
                #self.table.insertRow(row_count-1)
                self.table.setItem(row_count-1, 0, name_entry)
                year_entry = QTableWidgetItem(year)
                year_entry.setFlags(Qt.NoItemFlags)
                self.table.setItem(row_count-1, 1, year_entry)
                self.table.setItem(row_count-1, 2, maxres_entry)
                
                self.table.setItem(row_count-1, 3, checkbox_entry)
                
                
                if i < len(datasets)-1:
                    self.table.setRowCount(row_count+1)
            self.table.resizeColumnsToContents()
            
    def checkboxState(self, cbox):
        state = cbox.checkState()
        QgsMessageLog.logMessage('State now: '+str(state),
                                 'geocubes_plugin',
                                 Qgis.Info)
        if state == 0:
            self.stateNegative(cbox)
        elif state == 2:
            self.statePositive(cbox)
    
            
    def stateNegative(self, cbox):
        QgsMessageLog.logMessage('Row of this cbox: '+str(cbox.row()),
                                 'geocubes_plugin',
                                 Qgis.Info)
    
    def statePositive(self, cbox):
        QgsMessageLog.logMessage('Row of this cbox: '+str(cbox.row()),
                                 'geocubes_plugin',
                                 Qgis.Info)
            
    def getData(self):
        extent = self.getExtent()
        data_url = (self.url_base + "/clip/" + self.resolution +
                    "/mvmi-koivu/bbox:" + self.formatExtent(extent) + "/2009")
        raster_layer = QgsRasterLayer(data_url, "fetched_rlayer")
        
        if not raster_layer.isValid():
            raise Exception('Raster layer is invalid.')
        else:
            QgsProject.instance().addMapLayer(raster_layer)
            
    def getExtent(self):
        output_extent = self.extent_box.outputExtent()
        return output_extent
        """
        print_string = "The current extent: {}".format(output_extent)
        
        QgsMessageLog.logMessage(output_extent,
                                 'geocubes_plugin',
                                 Qgis.Info)
        """
        
    def formatExtent(self,rectangle):
        formatted_extent = (str(rectangle.xMinimum())+','+str(rectangle.yMinimum())
                            +','+str(rectangle.xMaximum())+','+str(rectangle.yMaximum()))
        return formatted_extent           

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = GeocubesPluginDialog()
            self.url_base = "http://86.50.168.160/geocubes"
            self.table = self.dlg.tableWidget
            self.table.setSizeAdjustPolicy(
                    QAbstractScrollArea.AdjustToContents)
            #self.table.itemChanged.connect(lambda:self.checkboxState(item))
            self.table.itemChanged.connect(self.checkboxState)
            self.dlg.getContents.clicked.connect(self.setToTable)
            self.extent_box = self.dlg.mExtentGroupBox
            self.resolution_box = self.dlg.resolutionBox
            self.resolution_box.activated.connect(self.setResolution)
            self.data_button = self.dlg.getDataButton
            self.data_button.clicked.connect(self.getData)
            self.bBoxButton = self.dlg.getMapLayerBbox
            self.bBoxButton.clicked.connect(self.getExtent)
            
            self.canvas = self.iface.mapCanvas()
            
        resolutions = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        self.resolution_box.clear()
        self.resolution_box.addItems(str(resolution) for resolution in resolutions)
        self.resolution_box.setCurrentIndex(6)
        self.resolution = self.resolution_box.currentText()
        
        self.downloadables = []
        
        # initialising the extent box
        proj_crs = QgsCoordinateReferenceSystem('EPSG:3067')
        og_extent = self.canvas.extent()
        
        self.extent_box.setOriginalExtent(og_extent, self.canvas.mapSettings().destinationCrs())
        self.extent_box.setCurrentExtent(og_extent, proj_crs)
        self.extent_box.setOutputCrs(proj_crs)
        
        # make sure the table is empty on restart
        self.table.clear()
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
