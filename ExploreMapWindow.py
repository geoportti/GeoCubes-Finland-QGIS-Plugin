# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:18:46 2019

@author: tle
"""

#from qgis.gui import *
import requests
from qgis.PyQt.QtWidgets import (QAction, QMainWindow, QSizePolicy, QComboBox,
                                 QTextEdit, QDockWidget, QSlider, QLabel, QCheckBox)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsRasterLayer
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolEmitPoint


class ExploreMapWindow(QMainWindow):
    """This class offers a canvas and tools to preview and explore data 
        provided by Geocubes. Preview raster layers are fetched from the Geocubes
        cached WMTS server. The user can simply view the data or get legend info
        on a single point."""
    
    # the window is initiated with the Geocubes url base defined on the main plugin
    # this means that the base doesn't have to be manually changed here if it changes
    def __init__(self, url_base):
        QMainWindow.__init__(self)
        
        # creating map canvas, which draws the maplayers
        # setting up features like canvas color
        self.canvas = QgsMapCanvas()
        self.canvas.setMinimumSize(550, 700)
        self.canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.canvas.setCanvasColor(Qt.white)
        #self.canvas.enableAntiAliasing(True)
        
        self.url_base = url_base
        
        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        """'tile widths' refer to the Map proxy WMTS server's settings for displaying
        data of different resolutions. If I understood correctly, these values 
        (got by examining properties of a layer from that server in QGIS) are
        the thresholds at which a different resolution is loaded on the GRIDI-FIN
        tileset. The values represent the tile size in map units (meters). 
        
        Each tile widths is tied to the corresponding resolution, which is used
        to get the correct resolution legend info. The method is only an estimation,
        but ought to produce good enough results for this purpose.
        Smallest resolutions (1, 2, 5) are omitted since only some layers 
        have them. """
        self.tile_widths = {2560: 10, 5120: 20, 12800: 50, 25600: 100,
                            51200: 200, 128000: 500, 256000: 1000}
        
        # get all keys i.e. widths
        self.all_widths = [i for i in self.tile_widths]
        
        # creating background layer box and housing it with the hardcoded options
        self.bg_layer_box = QComboBox()
        # if ortokuva ever updates to newer versions, just change the year here
        bg_layers = ['Taustakartta', 'Ortokuva_2018', 'No reference layer']
        
        # set 'No reference layer' as the default option
        self.bg_layer_box.addItems(layer for layer in bg_layers)
        self.bg_layer_box.setCurrentIndex(2)
        self.bg_layer_box.currentIndexChanged.connect(self.addBackgroundLayer)
        
        # initialize the slider that will control BG layer opacity/transparency
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setSingleStep(1)
        self.opacity_slider.setMaximumWidth(100)
        self.opacity_slider.valueChanged.connect(self.setBackgroundMapOpacity)
        
        self.legend_checkbox = QCheckBox("Get attribute info on all layers")
        
        # explanatory texts for the different widgets are stored as label widgets
        bg_layer_label = QLabel(" Background: ")
        bg_opacity_label = QLabel(" BG opacity: ")
        data_label = QLabel("Data: ")
        spacing = QLabel(" ")
        
        # all of the data layers are housed in this combobox
        self.layer_box = QComboBox()
        self.layer_box.currentIndexChanged.connect(self.addLayer)
        
        # creating each desired action
        self.actionPan = QAction("Pan tool", self)
        self.actionLegend = QAction("Attribute info tool", self)
        self.actionCancel = QAction("Close window", self)
        self.actionZoom = QAction("Zoom to full extent", self)
        
        # these two work as on/off. the rest are clickable
        self.actionPan.setCheckable(True)
        self.actionLegend.setCheckable(True)
        
        # when actions are clicked, do corresponding function
        self.actionPan.triggered.connect(self.pan)
        self.actionLegend.triggered.connect(self.info)
        self.actionCancel.triggered.connect(self.cancel)
        self.actionZoom.triggered.connect(self.zoomToExtent)
        
        # defining two toolbars: first one houses layer and opacity selection
        # the other has all the tools and functions
        self.layers_toolbar = self.addToolBar("Select layers")
        self.layers_toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.layers_toolbar.setMovable(False)
        self.addToolBarBreak()
        self.tools_toolbar = self.addToolBar("Tools")
        self.tools_toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.tools_toolbar.setMovable(False)
        
        # change order here to change their placement on window
        # starting with the layer widgets and the corresponding label texts
        self.layers_toolbar.addWidget(data_label)
        self.layers_toolbar.addWidget(self.layer_box)
        self.layers_toolbar.addWidget(bg_layer_label)
        self.layers_toolbar.addWidget(self.bg_layer_box)
        self.layers_toolbar.addWidget(bg_opacity_label)
        self.layers_toolbar.addWidget(self.opacity_slider)
        self.layers_toolbar.addWidget(spacing)
        self.layers_toolbar.addWidget(self.legend_checkbox)

        # then setting all the canvas tools on the second toolbar
        self.tools_toolbar.addAction(self.actionLegend)
        self.tools_toolbar.addAction(self.actionPan)
        self.tools_toolbar.addAction(self.actionZoom)
        self.tools_toolbar.addAction(self.actionCancel)
        
        # a large text box that will house the legend info
        self.text_browser = QTextEdit("Legend will be shown here")
        self.text_browser.setReadOnly(True)
        
        # a dock widget is required for the text browser. Docked to main window
        dock_widget = QDockWidget()
        dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock_widget.setWindowTitle("Legend")
        dock_widget.setWidget(self.text_browser)
        
        self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
    
        # link actions to premade map tools
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(self.actionPan)
        
        self.toolClick = QgsMapToolEmitPoint(self.canvas)
        self.toolClick.canvasClicked.connect(self.getLegendInfo)
        
        # this is to ensure that the map isn't zoomed out everytime the layer changes
        self.first_start = True
        
        # this boolean is true while there is no active background layer
        # needed to ensure that e.g. opacity isn't attempted to be set on a nonexisting layer
        self.no_bg_layer_flag = True
        
        # set pantool as default
        self.pan()

    def pan(self):
        """Simply activates the tool and deactivates the other tool if active"""
        self.canvas.setMapTool(self.toolPan)
        # make sure the other button isn't checked to avoid confusion
        self.actionLegend.setChecked(False)
        
    def info(self):
        self.canvas.setMapTool(self.toolClick)
        self.actionPan.setChecked(False)
        
    def zoomToExtent(self):
        """zooms out/in so that the raster layer is centered"""
        self.canvas.setExtent(self.layer.extent())
        self.canvas.refresh()
        
    def setBackgroundMapOpacity(self):
        if self.no_bg_layer_flag:
            return
        else:
            self.bg_layer.renderer().setOpacity(self.getBackgroundMapOpacity())
            self.canvas.refresh()
        
    def getBackgroundMapOpacity(self):
        """Returns the current BG layer opacity as a double [0, 1]. Slider only
            accepts integers, therefore the initial value is divided by hundred."""
        return (self.opacity_slider.value()/100)
        
    def showCanvas(self, all_datasets):
        """Called to activate the the window. Input is all of the datasets on 
            the Geocubes server as a dictionary (see main plugin py-file). First a
            default layer (background map, which is on the WMTS server
            but not on Geocubes files) is inserted to the combobox. Then the 
            keys of the dictionary (which are in format layer_name;year) are inserted."""
            
        # empty box on restart
        self.layer_box.clear()
        self.all_datasets = all_datasets
        self.no_bg_layer_flag = True
        
        for key in self.all_datasets:
            self.layer_box.addItem(key)
        
        # zoom to the full extent of the current map
        self.zoomToExtent()
        
        # default values set
        self.text_browser.setText("Legend will be shown here")
        self.bg_layer_box.setCurrentIndex(2)
        self.opacity_slider.setValue(50)
        self.show()
        
    def getLegendInfo(self, point):
        """Activated when the canvas is clicked. The click returns a point, which
            is parsed to a string of X and Y coordinates separated by a comma.
            An url to get legend info on this point is formed and used.
            If the request is succesful, the response string is decoded and passed
            to be inserted to the text browser."""
        formatted_point = str(int(point.x()))+","+str(int(point.y()))
        
        
        url = self.formLegendUrl(formatted_point)
        
        if not url:
            return
        
        response = requests.get(url, timeout=6)
        
        # 200 = succesful request
        # the field won't be updated in case of a failed request
        if response.status_code == 200:
            legend_string = response.content.decode("utf-8")
            self.setTextToBrowser(legend_string)
        
    def setTextToBrowser(self, string):
        """Formats and inserts legend text to the browser. Input is string of 
        raw text data. This is split at semicolons if there are multiple features."""
        
        # empty on multiple clicks
        self.text_browser.clear()
        strings = string.split(';')
        
        # no need for a loop if there's only one line
        if len(strings) == 1:
            self.text_browser.setText(string)
        else:
            for text_string in strings:
                # appending allows to insert multi-line texts
                self.text_browser.append(text_string)
            
    
    def formLegendUrl(self, formatted_point):
        """Forms an url for querying legend data on a specific coordinate point.
            Data is queried either from the currently selected layer or, if selected
            by the user, from all available layers."""
        key = self.layer_box.currentText()
        resolution = self.getResolutionFromExtent()
        
        if not key:
            return
        
        if not resolution:
            resolution = 100

        if self.legend_checkbox.isChecked():
            layer_name = "all"
            year = "2015"
        else:
            value = self.all_datasets[key]
            layer_name, year = value[0], value[3]
        
        url = (self.url_base + "/legend/"+str(resolution)+"/" +
                     layer_name +"/" + formatted_point
                    + "/" + year)
        
        return url
    
    def getResolutionFromExtent(self):
        """Estimates the resolution of the imagery currently viewed by user
         based on the width of the canvas. Returns said resolution. Used by
         the legend tool to get info of the correct dataset."""
        # extent as a QgsRectangle
        canvas_extent = self.canvas.extent()
        
        # width (in meters, since CRS is EPSG:3067) of the current canvas view
        width = canvas_extent.xMaximum()-canvas_extent.xMinimum()
        
        # find the width threshold closest to the current one
        try:
            closest_width = min(self.all_widths, key=lambda x:abs(x-width))
        except Exception:
            return
        
        # use the width key to get the corrensponding resolution
        closest_resolution = self.tile_widths[closest_width]
        
        return closest_resolution
    
    def addLayer(self):
        """Adds a new layer on the map canvas based on the selection on the combobox.
            Everything else is hardcoded, but the layer name of course changes.
            Layers are identified by name and year (i.e. km2_2018). These type
            of strings are formed first, then the whole url"""
        # often a layer already exists. If so, remove
        try:
            QgsProject.instance().removeMapLayer(self.layer)
        except Exception:
            pass
        
        key = self.layer_box.currentText()
        
        if not key:
            return
        # background map doesn't have a specific year attached to it
        if key == "Taustakartta":
            layer_name = key
        else:
            # the desired parameters are housed in the dictionary. Luckily the
            # combobox houses the keys to it. gets a tuple with four values
            value = self.all_datasets[key]
            # name is first value, year last. separated with an underscore
            layer_name = value[0] + "_" + value[3]
        
        url = ("http://86.50.168.160/ogiir_cache/wmts/1.0.0/" +
                "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                "png&layers=" + layer_name + "&styles=default&tileMatrixSet=GRIDI-FIN")
                

        
        self.layer = QgsRasterLayer("url="+url, 
                       'GEOCUBES DATALAYER - TEMPORARY', 'wms')
        
        if self.layer.isValid():
            QgsProject.instance().addMapLayer(self.layer, False)
            # if layer is valid and added to the instance, insert it to the canvas
            self.setMapLayers()
            # zoom to the full extent of the map if canvas is started for the first time
            if self.first_start:
                self.zoomToExtent()
                self.first_start = False
                
    def addBackgroundLayer(self):
        """Adds a background layer to help user locating what they want.
            This layer will be either background map (taustakarta), ortographic
            imagery or nothing at all. BG layer has an opacity value that set by
            the user. Function is called when user selects a layer on the
            combobox."""
        layer_name = self.bg_layer_box.currentText()
        
        # remove the old background layer, if one exists
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        
        # if user wants no background layer, return without setting a new layer
        if not layer_name or layer_name == 'No reference layer':
            self.no_bg_layer_flag = True
            self.canvas.refresh()
            return
        else:
            self.bg_layer = QgsRasterLayer("url=http://86.50.168.160/ogiir_cache/wmts/1.0.0/" +
                       "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                       "png&layers=" + layer_name.lower() + "&styles=default&tileMatrixSet=GRIDI-FIN", 
                       'GEOCUBES BG-LAYER - TEMPORARY', 'wms')
            
            if self.bg_layer.isValid():
                self.no_bg_layer_flag = False
                QgsProject.instance().addMapLayer(self.bg_layer, False)
                self.bg_layer.renderer().setOpacity(self.getBackgroundMapOpacity())
                self.setMapLayers()
                
    def setMapLayers(self):
        """Called anytime a new layer is added to the project instance.
        Setting layers to canvas decides what's shown to the user and in which
        order. If there's a background layer, it must be set before the data layer."""
        if self.no_bg_layer_flag:
            self.canvas.setLayers([self.layer])
        else:
            self.canvas.setLayers([self.bg_layer, self.layer])
        
        self.canvas.refresh()
        
    def cancel(self):
        self.close()
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either by buttons given or
            if the user finds some other way to close the window. 
            Deletes scrap maplayers."""
        try:
            QgsProject.instance().removeMapLayer(self.layer)
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        QMainWindow.closeEvent(self, event)