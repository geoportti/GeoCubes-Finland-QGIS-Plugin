# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 16:15:03 2019

@author: tle
"""
#from qgis.gui import *
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QSizePolicy
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import (QgsProject, QgsRasterLayer, QgsGeometry)
from qgis.gui import (QgsMapCanvas, QgsMapToolPan,
                      QgsMapToolEmitPoint, QgsRubberBand)

class PolygonMapWindow(QMainWindow):
    """Open a map window where the user can draw a polygon and use it to crop data.
       Shares a lot of similarities with MapWindow calss, but there're enough differences
        that I decided not to inherit from it."""
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

        # Qmainwindow requires a central widget. Canvas is placed
        self.setCentralWidget(self.canvas)
        
        # creating each desired action
        self.actionGet = QAction("Return polygon and close", self)
        self.actionPan = QAction("Pan tool", self)
        self.actionDraw = QAction("Polygon tool", self)
        self.actionConnect = QAction("Connect polygon", self)
        self.actionClear = QAction("Clear", self)
        self.actionCancel = QAction("Cancel and close", self)
        
        # these two function as on/off. the rest are clickable
        self.actionPan.setCheckable(True)
        self.actionDraw.setCheckable(True)
        
        # when actions are clicked, do corresponding function
        self.actionPan.triggered.connect(self.pan)
        self.actionDraw.triggered.connect(self.draw)
        self.actionClear.triggered.connect(self.clear)
        self.actionGet.triggered.connect(self.finishedSelection)
        self.actionConnect.triggered.connect(self.connect)
        self.actionCancel.triggered.connect(self.cancel)
        
        # toolbar at the top of the screen: houses actions as buttons
        # change order here to change their placement on toolbar
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.addAction(self.actionGet)
        self.toolbar.addAction(self.actionPan)
        self.toolbar.addAction(self.actionDraw)
        self.toolbar.addAction(self.actionConnect)
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
        # make sure the other button isn't checked to avoid confusion
        self.actionDraw.setChecked(False)
        
    def draw(self):
        """Activates draw tool"""
        self.canvas.setMapTool(self.toolDraw)
        self.actionPan.setChecked(False)
        
    def clear(self):
        self.toolDraw.reset()
    
    def connect(self):
        """Calls the polygon tool to connect an unconnected polygon"""
        self.toolDraw.finishPolygon()
        
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
        """Shows the map canvas with a vector background map for reference"""
        """
        url = ("https://vm0160.kaj.pouta.csc.fi/geoserver/ows?service=wfs&version=2.0.0"+ 
        "&request=GetFeature&typename=ogiir:maakuntajako_2018_4500k&pagingEnabled=true")
        #self.bg_layer = QgsVectorLayer(url, "BACKGROUND-REMOVE", "WFS")
        """
        self.bg_layer = QgsRasterLayer("url=https://vm0160.kaj.pouta.csc.fi/ogiir_cache/wmts/1.0.0/" +
                       "WMTSCapabilities.xml&crs=EPSG:3067&dpiMode=7&format=image/"+
                       "png&layers=taustakartta&styles=default&tileMatrixSet=GRIDI-FIN", 
                       'GEOCUBES POLYGON BG-LAYER - TEMPORARY', 'wms')
        
        if self.bg_layer.isValid():
            QgsProject.instance().addMapLayer(self.bg_layer, False)
            self.canvas.setExtent(self.bg_layer.extent())
            self.canvas.setLayers([self.bg_layer])
        self.show()
        
    def closeEvent(self, event):
        """Activated anytime Mapwindow is closed either programmatically or
            if the user finds some other way to close the window. Automatically
            finishes the polygon if it's unconnected."""
        try:
            QgsProject.instance().removeMapLayer(self.bg_layer)
        except Exception:
            pass
        self.toolDraw.finishPolygon()
        QMainWindow.closeEvent(self, event)
        
    def getPolygon(self):
        return self.toolDraw.getPoints()
    
    def getPolygonBbox(self):
        return self.toolDraw.getPolyBbox()
        
        
class PolygonMapTool(QgsMapToolEmitPoint):
    """This class holds a map tool to create a polygon from points got by clicking
        on the map window. Points are stored in a list of point geometries, which is returned to
        the main plugin for use."""
    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        # rubberband class gives the user visual feedback of the drawing
        self.rubberBand = QgsRubberBand(self.canvas, True)
        # setting up outline and fill color: both red
        self.rubberBand.setColor(QColor(235,36,21))
        # RGB color values, last value indicates transparency (0-255)
        self.rubberBand.setFillColor(QColor(255,79,66,140))
        self.rubberBand.setWidth(3)
        self.points = []
        # a flag indicating when a single polygon is finished
        self.finished = False
        self.poly_bbox = False
        self.double_click_flag = False
        self.reset()
      
    def reset(self):
        """Empties the canvas and the points gathered thus far"""
        self.rubberBand.reset(True)
        self.poly_bbox = False
        self.points.clear()

    def keyPressEvent(self, e):
        """Pressing ESC resets the canvas. Pressing enter connects the polygon"""
        if (e.key() == 16777216):
            self.reset()
        if (e.key() == 16777220):
            self.finishPolygon()
            
    def canvasDoubleClickEvent(self, e):
        self.double_click_flag = True
        self.finishPolygon()

    def canvasReleaseEvent(self, e):
        """Activated when user clicks on the canvas. Gets coordinates, draws
        them on the map and adds to the list of points."""
        if self.double_click_flag:
            self.double_click_flag = False
            return
        
        # if the finished flag is activated, the canvas will be must be reset
        # for a new polygon
        if self.finished:
            self.reset()
            self.finished = False
        
        self.click_point = self.toMapCoordinates(e.pos())
        
        self.rubberBand.addPoint(self.click_point, True)
        self.points.append(self.click_point)
        self.rubberBand.show()

        
    def finishPolygon(self):
        """Activated when by user or when the map window is closed without connecting
            the polygon. Makes the polygon valid by making first and last point
            the same. This is reflected visually. Up until now the user has been
            drawing a line: a polygon is created and shown on the map."""
        # nothing will happen if the code below has already been ran
        if self.finished:
            return
        # connecting the polygon is valid if there's already at least 3 points
        elif len(self.points)>2:
            first_point = self.points[0]
            self.points.append(first_point)
            self.rubberBand.closePoints()
            self.rubberBand.addPoint(first_point, True)
            self.finished = True
            # a polygon is created and added to the map for visual purposes
            map_polygon = QgsGeometry.fromPolygonXY([self.points])
            self.rubberBand.setToGeometry(map_polygon)
            # get the bounding box of this new polygon
            self.poly_bbox = self.rubberBand.asGeometry().boundingBox()
        else:
            self.finished = True
            
    def getPoints(self):
        """Returns list of PointXY geometries, i.e. the polygon in list form"""
        self.rubberBand.reset(True)
        return self.points
    
    def getPolyBbox(self):
        return self.poly_bbox