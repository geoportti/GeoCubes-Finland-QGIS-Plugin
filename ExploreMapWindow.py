# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:18:46 2019

@author: tle
"""

#from qgis.gui import *
import requests
from qgis.PyQt.QtWidgets import (QAction, QMainWindow, QSizePolicy, QComboBox,
                                 QTextEdit, QDockWidget)
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
        self.canvas.enableAntiAliasing(True)
        
        self.url_base = url_base
        
        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        # all of the layers are housed in this combobox
        self.layer_box = QComboBox()
        self.layer_box.currentIndexChanged.connect(self.addLayer)
        
        # creating each desired action
        self.actionPan = QAction("Pan tool", self)
        self.actionLegend = QAction("Legend info tool", self)
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
        
        # toolbar at the top of the screen: houses actions as buttons
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        
        # change order here to change their placement on window
        self.toolbar.addWidget(self.layer_box)
        self.toolbar.addAction(self.actionLegend)
        self.toolbar.addAction(self.actionPan)
        self.toolbar.addAction(self.actionZoom)
        self.toolbar.addAction(self.actionCancel)
        
        # a large text box that will house the legend info
        self.text_browser = QTextEdit("Legend will be shown here")
        
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
        
        # set pantool as default
        self.pan()

    def pan(self):
        """Simply activates the tool"""
        self.canvas.setMapTool(self.toolPan)
        # make sure the other button isn't checked to avoid confusion
        self.actionLegend.setChecked(False)
        
    def info(self):
        self.canvas.setMapTool(self.toolClick)
        self.actionPan.setChecked(False)
        
    def zoomToExtent(self):
        # zooms out/in so that the raster layer is centered
        self.canvas.setExtent(self.bg_layer.extent())
        self.canvas.refresh()
        
    def showCanvas(self, all_datasets):
        """Called to activate the the window. Input is all of the datasets on 
            the Geocubes server as a dictionary (see main plugin py-file). First a
            default layer (background map, which is on the WMTS server
            but not on Geocubes files) is inserted to the combobox. Then the 
            keys of the dictionary (which are in format layer_name;year) are inserted."""
            
        # empty box on restart
        self.layer_box.clear()
        self.all_datasets = all_datasets
        self.layer_box.addItem("Taustakartta")
        
        for key in self.all_datasets:
            self.layer_box.addItem(key)
        
        self.zoomToExtent()
        self.text_browser.setText("Legend will be shown here")
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
            Data is queried either from the currently selected layer or, in the
            case on the background map, from all available layers."""
        key = self.layer_box.currentText()
        resolution = 10
        
        if not key:
            return
        
        # pintamaalaji lacks data on for much of Finland on the higher resolutions
        # hence, an exception is made
        if key == "Pintamaalaji;2018":
            resolution = 100
        if key == "Taustakartta":
            layer_name = "all"
            year = "2015"
        else:
            value = self.all_datasets[key]
            layer_name, year = value[0], value[3]
        
        url = (self.url_base + "/legend/"+str(resolution)+"/" +
                     layer_name +"/" + formatted_point
                    + "/" + year)
        
        return url
    
    def addLayer(self):
        """Adds a new layer on the map canvas based on the selection on the combobox.
            Everything else is hardcoded, but the layer name of course changes.
            Layers are identified by name and year (i.e. km2_2018). These type
            of strings are formed first, then the whole url"""
        # often a layer already exists. If so, remove
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
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
        
        self.bg_layer = QgsRasterLayer("url=http://86.50.168.160/ogiir_cache/wmts/1.0.0/" +
                       "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                       "png&layers=" + layer_name.lower() + "&styles=default&tileMatrixSet=GRIDI-FIN", 
                       'GEOCUBES BG-LAYER - TO BE REMOVED', 'wms')
        
        if self.bg_layer.isValid():
            QgsProject.instance().addMapLayer(self.bg_layer, False)
            self.canvas.setLayers([self.bg_layer])
            # zoom to the full extent of the map if canvas is started for the first time
            if self.first_start:
                self.zoomToExtent()
                self.first_start = False
        
    def cancel(self):
        self.close()
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either by buttons given or
            if the user finds some other way to close the window. 
            Deletes scrap maplayer."""
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        QMainWindow.closeEvent(self, event)