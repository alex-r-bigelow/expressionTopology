#!/usr/bin/env python
import sys, os, math
from PySide.QtGui import QApplication, QGraphicsScene, QGraphicsItem, QPen, QFont, QBrush, QCompleter, QTableWidgetItem, QColorDialog, QFileDialog
from PySide.QtCore import Qt, QFile, QRectF, QTimer
from PySide.QtUiTools import QUiLoader
from expressionFiles import SoftFile, TsdFile

class parametricPulseGraph(QGraphicsItem):
    COLOR_MAP = {}
    
    SPEED_LIMIT = 0.25  # we can only step through a quarter of the data at a time
    SLICE_PROPORTION = 0.1
    
    UNSLICED_THICKNESS = 3
    UNSLICED_OPACITY = 0.25
    SLICED_THICKNESS = 6
    SLICED_OPACITY = 0.75
    
    FULL_SIZE = 400
    SMALL_SIZE = 100
    
    LABEL_THRESHOLD = 150
    
    LABEL_FONT = QFont('Gill Sans',18)
    LABEL_FONT.setStyleHint(QFont.StyleHint.SansSerif)
    LABEL_PEN = QPen(Qt.black)
    LABEL_OPACITY = 0.75
    LABEL_PADDING = 10
    
    TEXT_FONT = QFont('Gill Sans', 14)
    TEXT_FONT.setStyleHint(QFont.StyleHint.SansSerif)
    TEXT_PEN = QPen(Qt.white)
    TEXT_OPACITY = 0.75
    
    BORDER_WIDTH = 2.0
    BORDER = QPen(Qt.black,BORDER_WIDTH)
    BACKGROUND = QBrush(Qt.black)
    BACKGROUND_OPACITY = 0.9
    
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
        
        self.isTop = False
        self.isLeft = False
        self.isRight = False
        self.isBottom = False
        
        self.width = parametricPulseGraph.FULL_SIZE
        self.height = parametricPulseGraph.FULL_SIZE
        
        if self.vectors == None:
            return
        
        for vlist in self.vectors.itervalues():
            for x0,y0,t0,x1,y1,t1 in vlist:
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
        
        if self.xmin == None or self.xmax == None or self.ymin == None or self.ymax == None:
            self.xmin = None
            self.xmax = None
            self.ymin = None
            self.ymax = None
            self.vectors = None
    
    def paint(self, painter, option, widget=None):
        normalRect = QRectF(0,0,self.width,self.height)
        rotatedRect = QRectF(0,-self.height,self.width,self.height)
        
        if self.isTop or self.isLeft or self.isRight or self.isBottom:
            painter.setFont(parametricPulseGraph.LABEL_FONT)
            painter.setPen(parametricPulseGraph.LABEL_PEN)
            painter.setOpacity(parametricPulseGraph.LABEL_OPACITY)
            
            if self.isTop:
                labelRect = QRectF(-self.height,-self.width,self.height-parametricPulseGraph.LABEL_PADDING,self.width)
                painter.rotate(90)
                painter.drawText(labelRect, Qt.AlignRight | Qt.AlignVCenter, self.xAttribute)
                painter.rotate(-90)
            if self.isBottom:
                labelRect = QRectF(self.height+parametricPulseGraph.LABEL_PADDING,-self.width,self.height,self.width)
                painter.rotate(90)
                painter.drawText(labelRect, Qt.AlignLeft | Qt.AlignVCenter, self.xAttribute)
                painter.rotate(-90)
            if self.isLeft:
                labelRect = QRectF(-self.width,0,self.width-parametricPulseGraph.LABEL_PADDING,self.height)
                painter.drawText(labelRect, Qt.AlignRight | Qt.AlignVCenter, self.yAttribute)
            if self.isRight:
                labelRect = QRectF(self.width+parametricPulseGraph.LABEL_PADDING,0,self.width,self.height)
                painter.drawText(labelRect, Qt.AlignLeft | Qt.AlignVCenter, self.yAttribute)
        
        painter.setPen(parametricPulseGraph.BORDER)
        painter.setOpacity(parametricPulseGraph.BACKGROUND_OPACITY)
        painter.drawRect(normalRect)
        painter.fillRect(normalRect,parametricPulseGraph.BACKGROUND)
        if self.vectors != None and (self.xmax != self.xmin or self.ymax != self.ymin):
            # Draw vectors
            for cat,color in parametricPulseGraph.COLOR_MAP.iteritems():
                if not self.vectors.has_key(cat):
                    continue
                if self.xmax == self.xmin:
                    xScale = None
                else:
                    xScale = self.width / (self.xmax-self.xmin)
                if self.ymax == self.ymin:
                    yScale = None
                else:
                    yScale = self.height / (self.ymax-self.ymin)
                for x0,y0,t0,x1,y1,t1 in self.vectors[cat]:
                    if xScale == None:
                        x0 = self.width/2
                        x1 = self.width/2
                    else:
                        x0 = (x0-self.xmin)*xScale
                        x1 = (x1-self.xmin)*xScale
                    if yScale == None:
                        y0 = self.height/2
                        y1 = self.height/2
                    else:
                        y0 = (y0-self.ymin)*yScale
                        y1 = (y1-self.ymin)*yScale
                    
                    painter.setOpacity(parametricPulseGraph.UNSLICED_OPACITY)
                    painter.setPen(QPen(color,parametricPulseGraph.UNSLICED_THICKNESS))
                    painter.drawLine(x0,y0,x1,y1)
                    
                    if t0 == None or t1 == None:
                        return
                    
                    startTime = max(parametricPulseGraph.CURRENT_TIME-parametricPulseGraph.SLICE_DURATION,t0)
                    endTime = min(parametricPulseGraph.CURRENT_TIME+parametricPulseGraph.SLICE_DURATION,t1)
                    
                    if not endTime <= startTime:
                        startTime = (startTime-t0)/(t1-t0)
                        endTime = (endTime-t0)/(t1-t0)
                        
                        xstart = (x1-x0)*startTime
                        xend = (x1-x0)*endTime
                        ystart = (y1-y0)*startTime
                        yend = (y1-y0)*endTime
                        painter.setOpacity(parametricPulseGraph.SLICED_OPACITY)
                        painter.setPen(QPen(color,parametricPulseGraph.SLICED_THICKNESS))
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
        else:
            painter.setFont(parametricPulseGraph.TEXT_FONT)
            painter.setPen(parametricPulseGraph.TEXT_PEN)
            painter.setOpacity(parametricPulseGraph.TEXT_OPACITY)
            if self.vectors == None:
                painter.drawText(normalRect,Qt.AlignHCenter | Qt.AlignVCenter, "No Data")
            else:
                painter.drawText(normalRect,Qt.AlignHCenter | Qt.AlignVCenter, "No Variation")
    
    def boundingRect(self):
        pensize = parametricPulseGraph.BORDER_WIDTH/2
        return QRectF(-pensize,-pensize,self.width+pensize,self.height+pensize)
        
    def mousePressEvent(self, event):
        self.parent.setTarget(self.xAttribute,self.yAttribute)
    
    @staticmethod
    def nextFrame():
        parametricPulseGraph.CURRENT_TIME += parametricPulseGraph.CURRENT_SPEED
        if parametricPulseGraph.CURRENT_TIME - parametricPulseGraph.SLICE_DURATION > parametricPulseGraph.TIME_END:
            parametricPulseGraph.CURRENT_TIME = parametricPulseGraph.TIME_START - parametricPulseGraph.SLICE_DURATION
    @staticmethod
    def updateTimes(start,end):
        # These values will change
        parametricPulseGraph.TIME_START = int(start)
        parametricPulseGraph.TIME_END = math.ceil(end)
        parametricPulseGraph.CURRENT_TIME = int(parametricPulseGraph.TIME_START + (parametricPulseGraph.TIME_END-parametricPulseGraph.TIME_START)*0.5)
        parametricPulseGraph.SLICE_DURATION = math.ceil((parametricPulseGraph.TIME_END-parametricPulseGraph.TIME_START)*parametricPulseGraph.SLICE_PROPORTION)  # really number of seconds before and after
        parametricPulseGraph.MIN_SPEED = 0
        parametricPulseGraph.MAX_SPEED = math.ceil((parametricPulseGraph.TIME_END-parametricPulseGraph.TIME_START)*parametricPulseGraph.SPEED_LIMIT)
        parametricPulseGraph.CURRENT_SPEED = math.ceil(parametricPulseGraph.MAX_SPEED*0.25)  # everything is moved forward this many seconds every frame (THAT speed is defined by Viz.FRAME_DURATION)

class multiViewPanel:
    def __init__(self, view, controller):
        self.view = view
        self.controller = controller
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        self.variables = {}
        self.variableOrder = []
        self.currentX = None
        self.currentY = None
    
    def addVariable(self, var):
        if not var in self.variables.iterkeys():
            p = parametricPulseGraph(self,var,var,self.controller.getVectors(var,var))
            self.scene.addItem(p)
            varGraphs = {var:p}    # stick in a placeholder for the diagonal
            for v,graphs in self.variables.iteritems():
                x = parametricPulseGraph(self,var,v,self.controller.getVectors(var,v))
                y = parametricPulseGraph(self,v,var,self.controller.getVectors(v,var))
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
        for i,x in enumerate(self.variableOrder):
            if x == self.currentX:
                xPos += padding
            
            yPos = 0
            for j,y in enumerate(self.variableOrder):
                self.variables[x][y].isLeft = i == 0
                self.variables[x][y].isTop = j == 0
                self.variables[x][y].isRight = i == len(self.variableOrder)-1
                self.variables[x][y].isBottom = j == len(self.variableOrder)-1
                
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
    
class Viz:
    FRAME_DURATION = 1000/30 # 30 FPS
    DEFAULT_COLOR = Qt.lightGray
    def __init__(self):
        self.loadedPaths = set()
        self.dataSources = []
        self.genes = set()
        
        self.loader = QUiLoader()
        infile = QFile("expressionTopology.ui")
        infile.open(QFile.ReadOnly)
        self.window = self.loader.load(infile, None)
        infile.close()
        
        self.updateTimeSliders()
        
        # Main view
        self.multiPanel = multiViewPanel(self.window.graphicsView,self)
        
        # Events
        self.window.categoryTable.cellClicked.connect(self.changeColor)
        self.window.loadButton.clicked.connect(self.loadData)
        self.window.quitButton.clicked.connect(self.window.close)
        self.window.addButton.clicked.connect(self.addGene)
        self.window.geneBox.editTextChanged.connect(self.editGene)
        self.window.speedSlider.valueChanged.connect(self.changeSpeed)
        self.window.timeSlider.valueChanged.connect(self.changeTime)
        
        self.window.addButton.setEnabled(False)
        
        self.window.showFullScreen()
        #self.window.show()
        
        # Start timer
        
        # Update timer
        self.timer = QTimer(self.window)
        self.timer.timeout.connect(self.nextFrame)
        self.timer.start(Viz.FRAME_DURATION)
    
    def changeColor(self, row, column):
        if column == 1:
            col = QColorDialog.getColor()
            parametricPulseGraph.COLOR_MAP[self.window.categoryTable.item(row,0).text()] = col
            self.window.categoryTable.item(row,1).setBackground(col)
            self.multiPanel.scene.update()
    
    def addGene(self):
        g = self.window.geneBox.currentText()
        if g in self.genes:
            t = self.window.addButton.text()
            if t == 'Add':
                self.multiPanel.addVariable(g)
                self.window.addButton.setText('Remove')
            else:
                self.multiPanel.removeVariable(g)
                self.window.addButton.setText('Add')
    
    def editGene(self):
        g = self.window.geneBox.currentText()
        if g in self.genes:
            if self.multiPanel.variables.has_key(g):
                self.window.addButton.setText('Remove')
            else:
                self.window.addButton.setText('Add')
            self.window.addButton.setEnabled(True)
        else:
            self.window.addButton.setEnabled(False)
    
    def getVectors(self, x, y):
        vectors = {}
        for s in self.dataSources:
            vectors.update(s.getVectors(x,y))
        return vectors
    
    def nextFrame(self):
        if parametricPulseGraph.CURRENT_SPEED > 0:
            parametricPulseGraph.nextFrame()
            self.window.timeSlider.setSliderPosition(parametricPulseGraph.CURRENT_TIME)
            self.multiPanel.scene.update()
    
    def updateTimeSliders(self):
        self.window.timeSlider.setMinimum(parametricPulseGraph.TIME_START)
        self.window.timeSlider.setMaximum(parametricPulseGraph.TIME_END)
        self.window.timeSlider.setSliderPosition(parametricPulseGraph.CURRENT_TIME)
        self.window.timeSlider.setSingleStep(1)
        self.window.timeSlider.setPageStep(parametricPulseGraph.CURRENT_SPEED)
        self.window.speedSlider.setMinimum(parametricPulseGraph.MIN_SPEED)
        self.window.speedSlider.setMaximum(parametricPulseGraph.MAX_SPEED)
        self.window.speedSlider.setSliderPosition(parametricPulseGraph.CURRENT_SPEED)
        self.window.speedSlider.setSingleStep(1)
        self.window.speedSlider.setPageStep(int(0.1*parametricPulseGraph.MAX_SPEED))
    
    def changeSpeed(self):
        parametricPulseGraph.CURRENT_SPEED = self.window.speedSlider.value()
    
    def changeTime(self):
        parametricPulseGraph.CURRENT_TIME = self.window.timeSlider.value()
        self.multiPanel.scene.update()
    
    def loadData(self):
        fileNames = QFileDialog.getOpenFileNames(caption=u"Open expression data file", filter=u"SOFT (*.soft);;Time Series Data (*.tsd)")[0]  #;;Comma separated value (*.csv);;Column separated data (*.dat)
        if len(fileNames) == 0:
            return
        
        for f in fileNames:
            if f in self.loadedPaths:
                continue
            ext = os.path.splitext(f)[1].lower()
            fObj = None
            if ext == '.soft':
                fObj = SoftFile(f)
            elif ext == '.tsd':
                fObj = TsdFile(f)
            #elif ext == '.csv':
            #    self.dataSources.append(CsvFile(f))
            #elif ext == '.dat':
            #    self.dataSources.append(DatFile(f))
            else:
                continue
            self.dataSources.append(fObj)
            if len(self.loadedPaths) == 0:
                low,high = fObj.timeRange()
                parametricPulseGraph.updateTimes(low,high)
            else:
                low,high = fObj.timeRange()
                parametricPulseGraph.updateTimes(min(low,parametricPulseGraph.TIME_START),max(high,parametricPulseGraph.TIME_END))
            self.updateTimeSliders()
            self.loadedPaths.add(f)
        
        # Update gene box
        self.genes = set()
        for s in self.dataSources:
            self.genes.update(s.geneList())
        geneList = list(self.genes)
        self.window.geneBox.clear()
        self.window.geneBox.addItems(geneList)
        completer = QCompleter(geneList)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.window.geneBox.setCompleter(completer)
        
        # Update class table
        parametricPulseGraph.COLOR_MAP = {}
        for r in xrange(self.window.categoryTable.rowCount()):
            parametricPulseGraph.COLOR_MAP[self.window.categoryTable.item(r,0).text()] = self.window.categoryTable.item(r,1).background().color()
        for s in self.dataSources:
            for c in s.classList():
                if not parametricPulseGraph.COLOR_MAP.has_key(c):
                    parametricPulseGraph.COLOR_MAP[c] = Viz.DEFAULT_COLOR
        self.window.categoryTable.clear()
        self.window.categoryTable.setRowCount(len(parametricPulseGraph.COLOR_MAP))
        self.window.categoryTable.setColumnCount(2)
        
        for r,(t,c) in enumerate(sorted(parametricPulseGraph.COLOR_MAP.iteritems())):
            self.window.categoryTable.setItem(r,0,QTableWidgetItem(t))
            cItem = QTableWidgetItem("")
            cItem.setBackground(c)
            self.window.categoryTable.setItem(r,1,cItem)

if __name__ == '__main__':
    parametricPulseGraph.updateTimes(0,100)
    app = QApplication(sys.argv)
    window = Viz()
    sys.exit(app.exec_())