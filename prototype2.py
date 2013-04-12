#!/usr/bin/env python
import argparse, sys, math
from PySide.QtGui import QApplication, QGraphicsScene, QGraphicsItem, QPen, QFont, QBrush, QCompleter
from PySide.QtCore import Qt, QFile, QRectF
from PySide.QtUiTools import QUiLoader
from soft import SoftFile

def to_5_sig_figs(x):
    # TODO
    return str(x)

class parametricPulseGraph(QGraphicsItem):
    COLOR_MAP = {}
    THICKNESS = 6
    
    MOUSED_CATEGORY = None
    MOUSED_PEN = QPen(Qt.white,THICKNESS)
    
    SLICE_DELTA = 0.1
    SLICE_START = 0.0
    SLICE_END = 0.2
    UNSLICED_OPACITY = 0.5
    SLICED_OPACITY = 0.75
    
    FULL_SIZE = 300
    SMALL_SIZE = 100
    
    LABEL_THRESHOLD = 200
    
    TEXT_FONT = QFont('Helvetica', 9)
    TEXT_PEN = QPen(Qt.gray)
    TEXT_OPACITY = 0.5
    BACKGROUND = QBrush(Qt.lightGray)
    
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
        for x0,y0,x1,y1 in self.vectors.itervalues():
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
        rotatedRect = QRectF(0,-self.height,self.width,0)
        
        painter.fillRect(normalRect,parametricPulseGraph.BACKGROUND)
        if self.vectors != None:
            # Draw vectors
            for cat,pen in parametricPulseGraph.COLOR_MAP.iteritems():
                if cat == parametricPulseGraph.MOUSED_CATEGORY:
                    painter.setPen(parametricPulseGraph.MOUSED_PEN)
                else:
                    painter.setPen(pen)
                xScale = self.width / (self.xmax-self.xmin)
                yScale = self.height / (self.ymax-self.ymin)
                x0,y0,x1,y1 = self.vectors[cat]
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
                painter.drawText(normalRect,Qt.AlignCenter | Qt.AlignTop, to_5_sig_figs(self.ymax))
                painter.drawText(normalRect,Qt.AlignCenter | Qt.AlignBottom, to_5_sig_figs(self.ymin))
                painter.rotate(90)
                painter.drawText(rotatedRect,Qt.AlignCenter | Qt.AlignTop, to_5_sig_figs(self.xmax))
                painter.drawText(rotatedRect,Qt.AlignCenter | Qt.AlignBottom, to_5_sig_figs(self.xmin))
    
    @staticmethod
    def updateValues():
        parametricPulseGraph.SLICE_START += parametricPulseGraph.SLICE_DELTA
        if parametricPulseGraph.SLICE_START >= 1.0:
            parametricPulseGraph.SLICE_START = -parametricPulseGraph.SLICE_DELTA
        parametricPulseGraph.SLICE_END = parametricPulseGraph.SLICE_START+parametricPulseGraph.SLICE_DELTA
    
    def boundingRect(self):
        return QRectF(self.x(),self.y(),self.width,self.height)
    
    def mouseReleaseEvent(self, event):
        self.parent.setTarget(self.xAttribute,self.yAttribute)

class multiViewPanel:
    def __init__(self, view, data):
        self.view = view
        self.data = data
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        self.variables = {}
        self.variableOrder = []
        self.currentX = None
        self.currentY = None
    
    def addVariable(self, var):
        if not var in self.variables.iterkeys():
            varGraphs = {var:parametricPulseGraph(self,var,var,None)}    # stick in a placeholder for the diagonal
            for v,graphs in self.variables.iteritems():
                x = parametricPulseGraph(self,var,v,self.data.getVectors(var,v))
                y = parametricPulseGraph(self,var,v,self.data.getVectors(v,var))
                self.scene.addItem(x)
                self.scene.addItem(y)
                varGraphs[v] = x
                graphs[var] = y
            self.variables[var] = varGraphs
            self.variableOrder.append(var)
        self.updateView()
    
    def removeVariable(self, var):
        self.variableOrder.remove(var)
        del self.variables[var]
        for v in self.variableOrder:
            del self.variables[v][var]
        if self.currentX == var or self.currentY == var:
            self.noTarget()
    
    def noTarget(self):
        self.currentX = None
        self.currentY = None
        self.updateView()
    
    def setTarget(self, x, y):
        self.currentX = x
        self.currentY = y
        self.updateView()
    
    def updateView(self):
        # TODO: get these sizes dynamically
        xMax = 600
        yMax = 600
        if self.currentX == None and self.currentY == None:
            if len(self.variables) == 1:
                xPadding = max(0,(xMax-parametricPulseGraph.SMALL_SIZE)/2)
                yPadding = max(0,(yMax-parametricPulseGraph.SMALL_SIZE)/2)
            else:
                xPadding = max(0,(xMax-parametricPulseGraph.SMALL_SIZE*len(self.variables))/(2*len(self.variables)))
                yPadding = max(0,(yMax-parametricPulseGraph.SMALL_SIZE*len(self.variables))/(2*len(self.variables)))
            for i,x in enumerate(self.variableOrder):
                for j,y in enumerate(self.variableOrder):
                    self.variables[x][y].setPos((2*i+1)*xPadding,(2*j+1)*yPadding)
                    self.variables[x][y].width = parametricPulseGraph.SMALL_SIZE
                    self.variables[x][y].height = parametricPulseGraph.SMALL_SIZE
        elif len(self.variables) == 1:
            assert self.currentX == self.variableOrder[0] and self.currentY == self.variableOrder[0]
            xPadding = max(0,(xMax-parametricPulseGraph.FULL_SIZE)/2)
            yPadding = max(0,(yMax-parametricPulseGraph.FULL_SIZE)/2)
            self.variables[self.currentX][self.currentY].setPos(xPadding,yPadding)
            self.variables[self.currentX][self.currentY].width = parametricPulseGraph.FULL_SIZE
            self.variables[self.currentX][self.currentY].height = parametricPulseGraph.FULL_SIZE
        else:
            others=len(self.variables)-1
            xPadding = max(0,(xMax-parametricPulseGraph.FULL_SIZE-others*parametricPulseGraph.SMALL_SIZE)/(2*others))
            yPadding = max(0,(yMax-parametricPulseGraph.FULL_SIZE-others*parametricPulseGraph.SMALL_SIZE)/(2*others))
            
            specialPadding = (parametricPulseGraph.FULL_SIZE-parametricPulseGraph.SMALL_SIZE)/2
            
            passedX = False
            for i,x in enumerate(self.variableOrder):
                if not passedX:
                    left = i*parametricPulseGraph.SMALL_SIZE + 2*i*xPadding
                else:
                    left = (i-1)*parametricPulseGraph.SMALL_SIZE + 2*(i-1)*xPadding + parametricPulseGraph.FULL_SIZE
                if x != self.currentX:
                    left += xPadding
                else:
                    left += specialPadding
                passedY = False
                for j,y in enumerate(self.variableOrder):
                    if not passedY:
                        top = j*parametricPulseGraph.SMALL_SIZE + 2*j*yPadding
                    else:
                        top = (j-1)*parametricPulseGraph.SMALL_SIZE + 2*(j-1)*yPadding + parametricPulseGraph.FULL_SIZE
                    if y != self.currentY:
                        top += yPadding
                    else:
                        top += specialPadding
                    
                    if y == self.currentY and x == self.currentX:
                        # in the case we're actually at the target graph, we don't want any padding
                        self.variables[x][y].setPos(left-specialPadding,top-specialPadding)
                        self.variables[x][y].width = parametricPulseGraph.FULL_SIZE
                        self.variables[x][y].height = parametricPulseGraph.FULL_SIZE
                    else:
                        self.variables[x][y].setPos(left,top)
                        self.variables[x][y].width = parametricPulseGraph.SMALL_SIZE
                        self.variables[x][y].height = parametricPulseGraph.SMALL_SIZE
class Viz:
    def __init__(self, data):
        self.data = data
        
        self.loader = QUiLoader()
        infile = QFile("prototype2.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
                
        self.window.geneBox.addItems(self.data.geneList)
        completer = QCompleter(self.data.geneList)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.window.geneBox.setCompleter(completer)
        
        self.window.geneBox.clearEditText()
        self.window.addButton.setEnabled(False)
        
        self.multiPanel = multiViewPanel(self.window.graphicsView,self.data)
        
        self.window.quitButton.clicked.connect(self.window.close)
        self.window.addButton.clicked.connect(self.addGene)
        self.window.geneBox.editTextChanged.connect(self.editGene)
        
        #self.window.showFullScreen()
        self.window.show()
    
    def addGene(self):
        g = self.window.geneBox.currentText()
        if g in self.data.geneList:
            t = self.window.addButton.text()
            if t == 'Add':
                self.multiPanel.addVariable(g)
                self.window.addButton.setText('Remove')
            else:
                self.multiPanel.removeVariable(g)
                self.window.addButton.setText('Add')
    
    def editGene(self):
        g = self.window.geneBox.currentText()
        if g in self.data.geneList:
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