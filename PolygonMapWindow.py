# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 16:15:03 2019

@author: tle
"""
#from qgis.gui import *
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QSizePolicy
from qgis.PyQt.QtCore import Qt, pyqtSignal
#from PyQt5.QtGui import QFont
from qgis.core import (QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
                       QgsTextFormat, QgsTextBufferSettings, QgsProject,
                       QgsVectorLayer)
from qgis.gui import (QgsMapCanvas, QgsMapToolPan,
                      QgsMapToolEmitPoint, QgsRubberBand)

class PolygonMapWindow(QMainWindow):
    # signal emitted when polygons succesfully selected
    finished = pyqtSignal()
    
    def __init__(self):
        QMainWindow.__init__(self)
        
        # creating map canvas, which draws the maplayers
        # setting up features like canvas color
        self.canvas = QgsMapCanvas()
        self.canvas.setMinimumSize(550, 700)
        self.canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)
        
        """
        # empty list for selected polygons
        #self.selected_features = []
        
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
        """
        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        # creating each desired action
        self.actionGet = QAction("Return polygon and close", self)
        self.actionPan = QAction("Pan tool", self)
        self.actionDraw = QAction("Polygon draw tool", self)
        self.actionClear = QAction("Clear polygon", self)
        self.actionCancel = QAction("Cancel and close", self)
        
        # these two function as on/off. the rest are clickable
        self.actionPan.setCheckable(True)
        self.actionDraw.setCheckable(True)
        
        # when actions are clicked, do corresponding function
        self.actionPan.triggered.connect(self.pan)
        self.actionDraw.triggered.connect(self.draw)
        self.actionClear.triggered.connect(self.clear)
        self.actionGet.triggered.connect(self.finishedSelection)
        self.actionCancel.triggered.connect(self.cancel)
        
        # toolbar at the top of the screen: houses actions as buttons
        # change order here to change their placement on window
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.actionGet)
        self.toolbar.addAction(self.actionPan)
        self.toolbar.addAction(self.actionDraw)
        self.toolbar.addAction(self.actionClear)
        self.toolbar.addAction(self.actionCancel)

        # link actions to premade map tools
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(self.actionPan)
        self.toolDraw = PolygonMapTool(self.canvas)
        self.toolDraw.setAction(self.actionDraw)

        # set draw tool by default
        self.draw()
        
    def pan(self):
        """Simply activates the tool"""
        self.canvas.setMapTool(self.toolPan)
        
    def draw(self):
        self.canvas.setMapTool(self.toolDraw)
        
    def clear(self):
        self.toolDraw.reset()
        
    def finishedSelection(self):
        """Activated when user clicks 'returns selection'. Closes window
            and emits signal to indicate the job is finished"""
        self.close()
        self.finished.emit()
        
    def cancel(self):
        """In case user changes their mind. Does the same as above, but doesn't
            emit signal."""
        self.close()
        
    def showCanvas(self):
        url = ("http://86.50.168.160/geoserver/ows?service=wfs&version=2.0.0"+ 
        "&request=GetFeature&typename=ogiir:maakuntajako_2018_4500k&pagingEnabled=true")
        self.bg_layer = QgsVectorLayer(url, "BACKGROUND-REMOVE", "WFS")
        
        if self.bg_layer.isValid():
            self.bg_layer.renderer().symbol().setColor(Qt.gray)
            QgsProject.instance().addMapLayer(self.bg_layer, False)
            self.canvas.setExtent(self.bg_layer.extent())
            self.canvas.setLayers([self.bg_layer])
        self.show()
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either programmatically or
            if the user finds some other way to close the window. Removes
            selection and deletes scrap maplayer."""
        #self.clear()
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        QMainWindow.closeEvent(self, event)
        
    def getPolygon(self):
        return self.toolDraw.getPoints()
        
        
class PolygonMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, True)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setFillColor(Qt.white)
        self.rubberBand.setWidth(1)
        self.points = []
        self.finished = False
        self.first_point = False
        self.reset()
      
    def reset(self):
        #self.startPoint = self.endPoint = None
        #self.isEmittingPoint = False
        self.rubberBand.reset(True)
        self.points.clear()

    def keyPressEvent(self, e):
        self.reset()

    def canvasPressEvent(self, e):
        if self.finished:
            self.reset()
            self.finished = False
            return
        
        self.click_point = self.toMapCoordinates(e.pos())

        self.rubberBand.addPoint(self.click_point, True)
        self.points.append((int(self.click_point.x()), int(self.click_point.y())))
        self.rubberBand.show()
      
    def canvasDoubleClickEvent(self, e):
        self.finishPolygon()
        
    def finishPolygon(self):
        if len(self.points)>0:
            first_point = self.points[0]
            self.points.append(first_point)
        self.rubberBand.closePoints()
        self.finished = True       
        
    def getPoints(self):
        return self.points