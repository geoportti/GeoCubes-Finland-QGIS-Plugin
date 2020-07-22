# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 10:18:46 2019

@author: tle
"""

#from qgis.gui import *
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QSizePolicy
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from qgis.core import (QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
                       QgsTextFormat, QgsTextBufferSettings, QgsProject,
                       QgsVectorLayer, QgsRasterLayer)
from qgis.gui import (QgsMapCanvas, QgsMapToolPan, QgsMapToolIdentifyFeature)


class MapWindow(QMainWindow):
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
        self.canvas.setParallelRenderingEnabled(True)

        # empty list for selected polygons
        self.selected_features = []
        
        # setting up label settings: object below houses all of them
        self.label_settings = QgsPalLayerSettings()
        
        # object for text settings
        text_format = QgsTextFormat()
        
        text_format.setFont(QFont("Helvetica", 12))
        text_format.setSize(7)
        
        # setting up a white buffer around the labels
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(0.65)
        buffer_settings.setColor(Qt.white)
        text_format.setBuffer(buffer_settings)
        
        # label settings:
        # fieldName = which field is shown as the label (currently Finnish name)
        # placement = labels can be placed differently in relation to one another
        #              - see documentation for details
        self.label_settings.setFormat(text_format)
        self.label_settings.fieldName = "namefin"
        self.label_settings.placement = 0
        self.label_settings.enabled = True
        
        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        # creating each desired action
        self.actionGet = QAction("Return selected and close", self)
        self.actionPan = QAction("Pan tool", self)
        self.actionSelect = QAction("Select tool", self)
        self.actionClear = QAction("Clear selection", self)
        self.actionCancel = QAction("Cancel and close", self)
        
        # these two function as on/off. the rest are clickable
        self.actionPan.setCheckable(True)
        self.actionSelect.setCheckable(True)
        
        # when actions are clicked, do corresponding function
        self.actionPan.triggered.connect(self.pan)
        self.actionSelect.triggered.connect(self.select)
        self.actionClear.triggered.connect(self.clearSelection)
        self.actionGet.triggered.connect(self.finishedSelection)
        self.actionCancel.triggered.connect(self.cancel)
        
        # toolbar at the top of the screen: houses actions as buttons
        # change order here to change their placement on window
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.actionGet)
        self.toolbar.addAction(self.actionPan)
        self.toolbar.addAction(self.actionSelect)
        self.toolbar.addAction(self.actionClear)
        self.toolbar.addAction(self.actionCancel)

        # link actions to premade map tools
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(self.actionPan)
        self.toolSelect = QgsMapToolIdentifyFeature(self.canvas)
        self.toolSelect.setAction(self.actionSelect)
        self.toolSelect.featureIdentified.connect(self.selectFeature)
        
        self.blocks_flag = False
        
        self.selection_rectangle = False
        
        # set select tool as default
        self.select()

    def pan(self):
        """Simply activates the tool"""
        self.canvas.setMapTool(self.toolPan)
        
    def select(self):
        self.canvas.setMapTool(self.toolSelect)
        
    def addLayer(self, layer):
        """Called when user click button on the main plugin: receives a vector
            layer, sets up labels & rendering parameters and shows the layer."""
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
        
    def addBlocksLayer(self, layer):
        self.selected_features.clear()
        self.blocks_flag = True
        
        self.layer = layer
        
        QgsProject.instance().addMapLayer(self.layer, False)
        
        self.layer.renderer().symbol().setColor(Qt.cyan)
        self.layer.renderer().symbol().setOpacity(0.30)
        
        # select tool needs a vector layer assigned to it
        self.toolSelect.setLayer(self.layer)
        self.canvas.setExtent(self.layer.extent())
        
        # set layer to canvas
        """
        url = ("https://vm0160.kaj.pouta.csc.fi/geoserver/ows?service=wfs&version=2.0.0"+ 
        "&request=GetFeature&typename=ogiir:maakuntajako_4500k&pagingEnabled=true")
        self.bg_layer = QgsVectorLayer(url, "BACKGROUND-REMOVE", "WFS")
        """
        self.bg_layer = QgsRasterLayer("url=https://vm0160.kaj.pouta.csc.fi/ogiir_cache/wmts/1.0.0/" +
                       "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                       "png&layers=taustakartta&styles=default&tileMatrixSet=GRIDI-FIN", 
                       'GEOCUBES BG-LAYER - TEMPORARY', 'wms')

        if self.bg_layer.isValid():
            QgsProject.instance().addMapLayer(self.bg_layer, False)
            self.canvas.setLayers([self.layer, self.bg_layer])
        else:
            self.canvas.setLayers([self.layer])
        
        self.show()
        
        
    def selectFeature(self, feat):
        """Activated when user clicks something on screen. This returns the
            clicked feature. The function does 2 things:
            1. selects the feature on the map / deselects if already selected
            2. adds features to a list in the same format (name, id_code) as 
                they're stored in the 'Admin areas box' in the main file """
        idx  = feat.id()
        if self.blocks_flag:
            xmin = feat[0]
            ymax = feat[1]
            label = str(xmin) + "|" + str(ymax) 
        else:
            code = feat[1]
            name = feat[2]
            label = name + "|" + code
        
        if label in self.selected_features:
            self.layer.deselect(idx)
            self.selected_features.remove(label)
        else:
            self.layer.select(idx)
            self.selected_features.append(label)
            
    def clearSelection(self):
        """Clear map selection and list on button click"""
        self.layer.removeSelection()
        self.selected_features.clear()
        
    def finishedSelection(self):
        """Activated when user clicks 'return selection'. Closes window
            and emits signal to indicate the job is finished"""
        self.close()
        self.finished.emit()
        
    def cancel(self):
        """In case user changes their mind. Does the same as above, but doesn't
            emit signal."""
        self.close()
        
    def getSelection(self):
        """Returns list of selected features (polygons)"""
        return self.selected_features
    
    def getSelectionBbox(self):
        return self.selection_rectangle
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either by buttons given or
            if the user finds some other way to close the window. Removes
            selection and deletes scrap maplayer."""
        self.selection_rectangle = self.layer.boundingBoxOfSelected()
        self.layer.removeSelection()
        QgsProject.instance().removeMapLayer(self.layer)
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        self.blocks_flag = False
        QMainWindow.closeEvent(self, event)
