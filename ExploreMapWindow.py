# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:18:46 2019

@author: tle
"""

#from qgis.gui import *
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QSizePolicy, QComboBox
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from qgis.core import (QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
                       QgsTextFormat, QgsTextBufferSettings, QgsProject,
                       QgsVectorLayer, QgsRasterLayer)
from qgis.gui import (QgsMapCanvas, QgsMapToolPan, QgsMapToolEmitPoint)


class ExploreMapWindow(QMainWindow):
    """This class offers a canvas and tools to select polygons from a vector
        layer provided by the main app."""
        
    # signal emitted when polygons succesfully selected
    finished = pyqtSignal()
    
    def __init__(self):
        QMainWindow.__init__(self)
        #self.setWindowFlags(Qt.CustomizeWindowHint)
        #self.setWindowFlags(Qt.WindowMinMaxButtonsHint)
        
        # creating map canvas, which draws the maplayers
        # setting up features like canvas color
        self.canvas = QgsMapCanvas()
        self.canvas.setMinimumSize(550, 700)
        self.canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.setSelectionColor(QColor(255,255,26,200))
        self.canvas.enableAntiAliasing(True)
        
        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        self.layer_box = QComboBox()
        self.layer_box.currentIndexChanged.connect(self.addLayer)
        
        # creating each desired action
        #self.actionGet = QAction("Return selected and close", self)
        self.actionPan = QAction("Pan tool", self)
        #self.actionSelect = QAction("Select tool", self)
        #self.actionClear = QAction("Clear selection", self)
        self.actionCancel = QAction("Cancel and close", self)
        
        # these two function as on/off. the rest are clickable
        self.actionPan.setCheckable(True)
        #self.actionSelect.setCheckable(True)
        
        # when actions are clicked, do corresponding function
        self.actionPan.triggered.connect(self.pan)
        #self.actionSelect.triggered.connect(self.select)
        #self.actionClear.triggered.connect(self.clearSelection)
        #self.actionGet.triggered.connect(self.finishedSelection)
        self.actionCancel.triggered.connect(self.cancel)
        
        # toolbar at the top of the screen: houses actions as buttons
        # change order here to change their placement on window
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        
        self.toolbar.addWidget(self.layer_box)
        #self.toolbar.addAction(self.actionGet)
        self.toolbar.addAction(self.actionPan)
        #self.toolbar.addAction(self.actionSelect)
        #self.toolbar.addAction(self.actionClear)
        self.toolbar.addAction(self.actionCancel)

        # link actions to premade map tools
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(self.actionPan)
        #self.toolSelect = QgsMapToolEmitPoint(self.canvas)
        #self.toolSelect.setAction(self.actionSelect)
        #self.toolSelect.featureIdentified.connect(self.selectFeature)
        
        self.first_start = True
        
        # set select tool as default
        self.pan()

    def pan(self):
        """Simply activates the tool"""
        self.canvas.setMapTool(self.toolPan)
        
    def showCanvas(self, all_datasets):
        self.layer_box.clear()
        self.all_datasets = all_datasets
        self.layer_box.addItem("Taustakartta")
        
        for key in self.all_datasets:
            self.layer_box.addItem(key)
            """
            value = self.all_datasets[key]
            new_value = (value[0], value[3])
            self.all_datasets[key] = new_value
            """
            
        #self.layer_box.setCurrentIndex(0)
        
        self.show()
        
        
    def addLayer(self):
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        
        key = self.layer_box.currentText()
        
        if not key:
            return
        if key == "Taustakartta":
            layer_name = key
        else:
            value = self.all_datasets[key]
            layer_name = value[0] + "_" + value[3]
        
        self.bg_layer = QgsRasterLayer("url=http://86.50.168.160/ogiir_cache/wmts/1.0.0/" +
                       "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                       "png&layers=" + layer_name.lower() + "&styles=default&tileMatrixSet=GRIDI-FIN", 
                       'GEOCUBES BG-LAYER - TO BE REMOVED', 'wms')
        
        if self.bg_layer.isValid():
            #self.bg_layer.renderer().symbol().setColor(QColor(170,170,170))
            QgsProject.instance().addMapLayer(self.bg_layer, False)
            self.canvas.setLayers([self.bg_layer])
            if self.first_start:
                self.canvas.setExtent(self.bg_layer.extent())
                self.first_start = False
    """
    def select(self):
        self.canvas.setMapTool(self.toolSelect)
        
    def addLayer(self, layer):
        Called when user click button on the main plugin: receives a vector
            layer, sets up labels & rendering parameters and shows the layer.
        # empty output list in case function is called multiple times
        self.selected_features.clear()
        self.selection_rectangle = False
        
        # layer into a self variable
        self.layer = layer
        
        # add layer to project: required to show it on screen
        # False = do not show the layer on the legend listing nor draw on main canvas
        QgsProject.instance().addMapLayer(self.layer, False)
        
        # set up visual stuff
        self.layer.setLabelsEnabled(True)
        layer_labeling = QgsVectorLayerSimpleLabeling(self.label_settings)
        self.layer.setLabeling(layer_labeling)
        self.layer.renderer().symbol().setColor(QColor(220,220,220))
        
        # select tool needs a vector layer assigned to it
        self.toolSelect.setLayer(self.layer)
        self.canvas.setExtent(self.layer.extent())
        
        # set layer to canvas
        self.canvas.setLayers([self.layer])
        
        # show to user
        self.show()
    """
    def finishedSelection(self):
        """Activated when user clicks 'return selection'. Closes window
            and emits signal to indicate the job is finished"""
        self.close()
        self.finished.emit()
        
    def cancel(self):
        """In case user changes their mind. Does the same as above, but doesn't
            emit signal."""
        self.close()
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either by buttons given or
            if the user finds some other way to close the window. Removes
            selection and deletes scrap maplayer."""
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        QMainWindow.closeEvent(self, event)