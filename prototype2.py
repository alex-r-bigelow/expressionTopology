#!/usr/bin/env python
import argparse, sys, math
from PySide.QtGui import QApplication, QGraphicsScene, QGraphicsItem, QPen, QFont, QBrush, QCompleter, QTableWidgetItem, QColor, QColorDialog
from PySide.QtCore import Qt, QFile, QRectF, QTimer
from PySide.QtUiTools import QUiLoader
from soft import SoftFile

class parametricPulseGraph(QGraphicsItem):
    COLOR_MAP = {}
    THICKNESS = 6
    
    MOUSED_CATEGORY = None
    MOUSED_PEN = QPen(Qt.white,THICKNESS)
    
    SLICE_DELTA = 0.05
    SLICE_START = 0.0
    SLICE_END = 0.3
    UNSLICED_OPACITY = 0.5
    SLICED_OPACITY = 0.75
    
    FULL_SIZE = 300
    SMALL_SIZE = 100
    
    LABEL_THRESHOLD = 150
    
    TEXT_FONT = QFont('Helvetica', 11)
    TEXT_PEN = QPen(Qt.white)
    TEXT_OPACITY = 0.5
    
    BORDER_WIDTH = 2.0
    BORDER = QPen(Qt.black,BORDER_WIDTH)
    BACKGROUND = QBrush(QColor(20,20,20,255))
    
    def __init__(self, parent, xAttribute, yAttribute, vectors=None):
        QGraphicsItem.__init__(self)
        self.parent = parent
        self.xAttribute = xAttribute
        self.yAttribute = yAttribute
        self.vectors = vectors
        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None
        
        self.width = parametricPulseGraph.FULL_SIZE
        self.height = parametricPulseGraph.FULL_SIZE
        
        if self.vectors == None:
            return
        for vlist in self.vectors.itervalues():
            for x0,y0,x1,y1 in vlist:
                if self.xmin == None:
                    self.xmin = min(x0,x1)
                    self.xmax = max(x0,x1)
                    self.ymin = min(y0,y1)
                    self.ymax = max(y0,y1)
                else:
                    self.xmin = min(self.xmin,x0,x1)
                    self.xmax = max(self.xmax,x0,x1)
                    self.ymin = min(self.ymin,y0,y1)
                    self.ymax = max(self.ymax,y0,y1)
    
    def paint(self, painter, option, widget=None):
        normalRect = QRectF(0,0,self.width,self.height)
        rotatedRect = QRectF(0,-self.height,self.width,self.height)
        
        painter.setPen(parametricPulseGraph.BORDER)
        painter.drawRect(normalRect)
        if self.vectors != None:
            painter.fillRect(normalRect,parametricPulseGraph.BACKGROUND)
            
            # Draw vectors
            for cat,color in parametricPulseGraph.COLOR_MAP.iteritems():
                if not self.vectors.has_key(cat):
                    continue
                if cat == parametricPulseGraph.MOUSED_CATEGORY:
                    painter.setPen(parametricPulseGraph.MOUSED_PEN)
                else:
                    painter.setPen(QPen(color,parametricPulseGraph.THICKNESS))
                xScale = self.width / (self.xmax-self.xmin)
                yScale = self.height / (self.ymax-self.ymin)
                for x0,y0,x1,y1 in self.vectors[cat]:
                    x0 = (x0-self.xmin)*xScale
                    y0 = (y0-self.ymin)*yScale
                    x1 = (x1-self.xmin)*xScale
                    y1 = (y1-self.ymin)*yScale
                    painter.setOpacity(parametricPulseGraph.UNSLICED_OPACITY)
                    painter.drawLine(x0,y0,x1,y1)
                    xstart = (x1-x0)*parametricPulseGraph.SLICE_START
                    xend = (x1-x0)*parametricPulseGraph.SLICE_END
                    ystart = (y1-y0)*parametricPulseGraph.SLICE_START
                    yend = (y1-y0)*parametricPulseGraph.SLICE_END
                    painter.setOpacity(parametricPulseGraph.SLICED_OPACITY)
                    painter.drawLine(x0+xstart,y0+ystart,x0+xend,y0+yend)
                
            # Draw labels
            if min(self.width,self.height) >= parametricPulseGraph.LABEL_THRESHOLD:
                painter.setFont(parametricPulseGraph.TEXT_FONT)
                painter.setPen(parametricPulseGraph.TEXT_PEN)
                painter.setOpacity(parametricPulseGraph.TEXT_OPACITY)
                painter.drawText(normalRect,Qt.AlignHCenter | Qt.AlignTop, "%s, %f" % (self.yAttribute,self.ymax))
                painter.drawText(normalRect,Qt.AlignHCenter | Qt.AlignBottom, "%s, %f" % (self.yAttribute,self.ymin))
                painter.rotate(90)
                painter.drawText(rotatedRect,Qt.AlignHCenter | Qt.AlignTop, "%s, %f" % (self.xAttribute,self.xmax))
                painter.drawText(rotatedRect,Qt.AlignHCenter | Qt.AlignBottom, "%s, %f" % (self.xAttribute,self.xmin))
    
    @staticmethod
    def updateValues():
        parametricPulseGraph.SLICE_START += parametricPulseGraph.SLICE_DELTA
        if parametricPulseGraph.SLICE_START >= 1.0:
            parametricPulseGraph.SLICE_START = -parametricPulseGraph.SLICE_DELTA
        parametricPulseGraph.SLICE_END = parametricPulseGraph.SLICE_START+parametricPulseGraph.SLICE_DELTA
    
    def boundingRect(self):
        pensize = parametricPulseGraph.BORDER_WIDTH/2
        return QRectF(-pensize,-pensize,self.width+pensize,self.height+pensize)
        
    def mousePressEvent(self, event):
        self.parent.setTarget(self.xAttribute,self.yAttribute)

class multiViewPanel:
    FRAME_DURATION = 1000/60 # 60 FPS
    def __init__(self, view, data):
        self.view = view
        self.data = data
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        self.variables = {}
        self.variableOrder = []
        self.currentX = None
        self.currentY = None
        
        # Update timer
        self.timer = QTimer(self.view)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start(multiViewPanel.FRAME_DURATION)
    
    def addVariable(self, var):
        if not var in self.variables.iterkeys():
            p = parametricPulseGraph(self,var,var,None)
            self.scene.addItem(p)
            varGraphs = {var:p}    # stick in a placeholder for the diagonal
            for v,graphs in self.variables.iteritems():
                x = parametricPulseGraph(self,var,v,self.data.getVectors(var,v))
                y = parametricPulseGraph(self,v,var,self.data.getVectors(v,var))
                self.scene.addItem(x)
                self.scene.addItem(y)
                varGraphs[v] = x
                graphs[var] = y
            self.variables[var] = varGraphs
            self.variableOrder.append(var)
        self.updateView()
    
    def removeVariable(self, var):
        self.variableOrder.remove(var)
        for v in self.variables[var].itervalues():
            self.scene.removeItem(v)
        del self.variables[var]
        for v in self.variableOrder:
            self.scene.removeItem(self.variables[v][var])
            del self.variables[v][var]
        if self.currentX == var or self.currentY == var:
            self.noTarget()
        else:
            self.updateView()
    
    def noTarget(self):
        self.currentX = None
        self.currentY = None
        self.updateView()
    
    def setTarget(self, x, y):
        if self.currentX == x and self.currentY == y:
            self.noTarget()
        else:
            self.currentX = x
            self.currentY = y
            self.updateView()
    
    def updateView(self):
        padding = (parametricPulseGraph.FULL_SIZE-parametricPulseGraph.SMALL_SIZE)/2
        xPos = 0
        for x in self.variableOrder:
            if x == self.currentX:
                xPos += padding
            
            yPos = 0
            for y in self.variableOrder:
                if x == self.currentX and y == self.currentY:
                    self.variables[x][y].setPos(xPos-padding,yPos)
                    self.variables[x][y].width = parametricPulseGraph.FULL_SIZE
                    self.variables[x][y].height = parametricPulseGraph.FULL_SIZE
                    yPos += parametricPulseGraph.FULL_SIZE
                else:
                    if y == self.currentY:
                        yPos += padding
                    self.variables[x][y].setPos(xPos,yPos)
                    self.variables[x][y].width = parametricPulseGraph.SMALL_SIZE
                    self.variables[x][y].height = parametricPulseGraph.SMALL_SIZE
                    yPos += parametricPulseGraph.SMALL_SIZE
                    if y == self.currentY:
                        yPos += padding
            
            xPos += parametricPulseGraph.SMALL_SIZE
            if x == self.currentX:
                xPos += padding
        self.scene.update()
    
    def updateValues(self):
        parametricPulseGraph.updateValues()
        self.scene.update()
class Viz:
    def __init__(self, data):
        self.data = data
        
        self.loader = QUiLoader()
        infile = QFile("prototype2.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
        
        # Gene box
        allGenes = self.data.geneList()
        self.window.geneBox.addItems(allGenes)
        completer = QCompleter(allGenes)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.window.geneBox.setCompleter(completer)
        
        self.window.geneBox.clearEditText()
        self.window.addButton.setEnabled(False)
        
        # Color picker
        self.allClasses = self.data.classList()
        self.window.categoryTable.setRowCount(len(self.allClasses))
        self.window.categoryTable.setColumnCount(2)
        parametricPulseGraph.COLOR_MAP = dict(zip(self.allClasses,[Qt.blue for x in xrange(len(self.allClasses))]))
        
        for r,c in enumerate(self.allClasses):
            self.window.categoryTable.setItem(r,0,QTableWidgetItem(c))
            cItem = QTableWidgetItem("")
            cItem.setBackground(QBrush(parametricPulseGraph.COLOR_MAP[c]))
            self.window.categoryTable.setItem(r,1,cItem)
        
        self.window.categoryTable.cellClicked.connect(self.changeColor)
        
        # Main view
        self.multiPanel = multiViewPanel(self.window.graphicsView,self.data)
        
        # Button events
        self.window.quitButton.clicked.connect(self.window.close)
        self.window.addButton.clicked.connect(self.addGene)
        self.window.geneBox.editTextChanged.connect(self.editGene)
        
        self.window.showFullScreen()
        #self.window.show()
    
    def changeColor(self, row, column):
        if column == 1:
            col = QColorDialog.getColor()
            parametricPulseGraph.COLOR_MAP[self.window.categoryTable.item(row,0).text()] = col
            self.window.categoryTable.item(row,1).setBackground(col)
    
    def addGene(self):
        g = self.window.geneBox.currentText()
        if g in self.data.genes:
            t = self.window.addButton.text()
            if t == 'Add':
                self.multiPanel.addVariable(g)
                self.window.addButton.setText('Remove')
            else:
                self.multiPanel.removeVariable(g)
                self.window.addButton.setText('Add')
    
    def editGene(self):
        g = self.window.geneBox.currentText()
        if g in self.data.genes:
            if self.multiPanel.variables.has_key(g):
                self.window.addButton.setText('Remove')
            else:
                self.window.addButton.setText('Add')
            self.window.addButton.setEnabled(True)
        else:
            self.window.addButton.setEnabled(False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualizes a .soft file')
    parser.add_argument('--in', type=str, dest="infile", required = True, help='Path to the .soft file.')
    
    args = parser.parse_args()
    
    s = SoftFile(args.infile)
    
    app = QApplication(sys.argv)
    window = Viz(s)
    sys.exit(app.exec_())