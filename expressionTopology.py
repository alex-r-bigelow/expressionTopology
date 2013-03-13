#!/usr/bin/env python
import argparse, os
import pyprocessing
from structures import rangeSet

# TODO: see http://labix.org/python-dateutil#head-ba5ffd4df8111d1b83fc194b97ebecf837add454 for inferring time from !subset_description fields, but it still gets some things like 'min' wrong

SIZE = (1280,1024)

BACKGROUND = (255,255,255)
AXES = (50,50,50)
EXP = (100,50,50,100)
EXP2 = (200,50,50,100)
SIM = (50,50,100,100)
SIM2 = (50,50,200,100)

PLOT_LEFT = 20
PLOT_RIGHT=1000
PLOT_TOP = 20
PLOT_BOTTOM = 1000

TEXTSIZE = 16
AXISSIZE = 5
TIMELINESIZE = 1
TIMESLICESIZE = 3

expData = {}
simData = {}

allHeaders = []
mins = {}
maxes = {}
xranges = {}
yranges = {}
colWidth = None
rowHeight = None

showExp = True
showSim = True

minTime = 0
maxTime = 0
t1 = None
t2 = None
spanProportion = 0.2
tspan = None
dt = 5
timeSteps = rangeSet()

noPlots = None
expOnly = None
simOnly = None
bothPlots = None

def setup():
    global colWidth,rowHeight,xranges,yranges,noPlots,expOnly,simOnly,bothPlots
    
    colWidth = (PLOT_RIGHT-PLOT_LEFT)/len(allHeaders)
    rowHeight = (PLOT_BOTTOM-PLOT_TOP)/len(allHeaders)
    xranges = {}
    yranges = {}
    for h,v in mins.iteritems():
        s = (maxes[h]-v)
        if s <= 0:
            s = 1.0
        xranges[h] = colWidth/s
        yranges[h] = rowHeight/s
    
    pyprocessing.size(PLOT_RIGHT+1,PLOT_BOTTOM+1)
    
    # noPlots
    print 'Drawing Axes...'
    pyprocessing.background(*BACKGROUND)
    drawAxes()
    pyprocessing.save('noPlots.png')
    noPlots = pyprocessing.loadImage('noPlots.png')
    
    # expOnly
    print 'Drawing Experimental Timelines...'
    # Can skip drawing Axes because we just did...
    pyprocessing.strokeWeight(TIMELINESIZE)
    pyprocessing.stroke(*EXP)
    drawLines(expData, timeSlice=False)
    #drawLines(simData, timeSlice=False)
    pyprocessing.save('expOnly.png')
    backPlot = pyprocessing.loadImage('expOnly.png')
    
    # simOnly
    print 'Drawing Simulation Timelines...'
    pyprocessing.background(*BACKGROUND)
    pyprocessing.image(noPlots,0,0)
    
    pyprocessing.strokeWeight(TIMELINESIZE)
    pyprocessing.stroke(*SIM)
    drawLines(simData, timeSlice=False)
    pyprocessing.save('simOnly.png')
    simOnly = pyprocessing.loadImage('simOnly.png')
    
    # bothPlots
    print 'Drawing both together...'
    pyprocessing.background(*BACKGROUND)
    pyprocessing.image(noPlots,0,0)
    
    pyprocessing.strokeWeight(TIMELINESIZE)
    pyprocessing.stroke(*EXP)
    drawLines(expData, timeSlice=False)
    pyprocessing.stroke(*SIM)
    drawLines(simData, timeSlice=False)
    pyprocessing.save('bothPlots.png')
    bothPlots = pyprocessing.loadImage('bothPlots.png')
    
    # global settings
    pyprocessing.size(*SIZE)
    font = pyprocessing.createFont('Gill Sans',TEXTSIZE)
    pyprocessing.textFont(font)
    pyprocessing.textAlign(pyprocessing.CENTER, pyprocessing.CENTER)
    pyprocessing.frameRate(5)

def drawAxes():
    pyprocessing.stroke(AXISSIZE)
    pyprocessing.stroke(*AXES)
    for c,ch in enumerate(allHeaders):
        for r,rh in enumerate(allHeaders):
            pyprocessing.fill(*BACKGROUND)
            pyprocessing.rect(PLOT_LEFT+c*colWidth,PLOT_TOP+r*rowHeight,colWidth,rowHeight)
            if c == r:
                pyprocessing.fill(*AXES)
                # TODO: center this...
                pyprocessing.text('Z',PLOT_LEFT+c*colWidth+colWidth/2,PLOT_TOP+r*rowHeight+rowHeight/2,colWidth,rowHeight)

def drawLines(dataSet, timeSlice=True, context=pyprocessing):
    for f,frames in dataSet.iteritems():
        t0 = None
        values0 = None
        if timeSlice:
            temp = timeSteps[t1:t2]
        else:
            temp = timeSteps
        for t in temp:
            if not frames.has_key(t):
                continue
            values = frames[t]
            if t0 != None:
                for c,ch in enumerate(allHeaders):
                    for r,rh in enumerate(allHeaders):
                        if c == r:
                            continue
                        pyprocessing.line(PLOT_LEFT+c*colWidth+(values0[ch]-mins[ch])*xranges[ch],
                                          PLOT_TOP+r*rowHeight+(values0[rh]-mins[rh])*yranges[rh],
                                          PLOT_LEFT+c*colWidth+(values[ch]-mins[ch])*xranges[ch],
                                          PLOT_TOP+r*rowHeight+(values[rh]-mins[rh])*yranges[rh])
            t0 = t
            values0 = values

def draw2dPlots(x,y,w,h):
    pyprocessing.fill(*BACKGROUND)
    if showExp:
        if showSim:
            pyprocessing.image(bothPlots,0,0)
        else:
            pyprocessing.image(expOnly,0,0)
    else:
        if showSim:
            pyprocessing.image(simOnly,0,0)
        else:
            pyprocessing.image(noPlots,0,0)
    
    pyprocessing.strokeWeight(TIMESLICESIZE)
    if showExp:
        pyprocessing.stroke(*EXP2)
        drawLines(expData)
    
    if showSim:
        pyprocessing.stroke(*SIM2)
        drawLines(simData)

def draw():
    global t1,t2
    pyprocessing.background(*BACKGROUND)
    draw2dPlots(50,50,width-100,height-100)
    t1 += dt
    t2 += dt
    if t1 >= maxTime:
        t2 = minTime
        t1 = minTime - tspan
    
    '''
    lights()
    translate(width / 2, height / 2);
    rotateY(mouse.x * PI / width);
    rotateZ(mouse.y * -PI / height);
    noStroke();
    fill(255, 255, 255);
    translate(0, -40, 0);
    drawCylinder(10, 180, 200, 16); # Draw a mix between a cylinder and a cone
    #drawCylinder(70, 70, 120, 16); # Draw a cylinder
    #drawCylinder(0, 180, 200, 4); # Draw a pyramid
    pass'''

'''def drawCylinder(topRadius, bottomRadius, tall, sides):
    angle = 0;
    angleIncrement = TWO_PI / sides;
    beginShape(QUAD_STRIP);
    for i in range(sides + 1):
        # normal(cos(angle),sin(angle),0)
        vertex(topRadius * cos(angle), 0, topRadius * sin(angle));
        vertex(bottomRadius * cos(angle), tall, bottomRadius * sin(angle));
        angle += angleIncrement;
    endShape();
    
    # If it is not a cone, draw the circular top cap
    if (topRadius != 0):
        angle = 0;
        beginShape(TRIANGLE_FAN);
        
        # Center point
        vertex(0, 0, 0);
        for i in range(sides + 1):
            vertex(topRadius * cos(angle), 0, topRadius * sin(angle));
            angle += angleIncrement;
        endShape();

    # If it is not a cone, draw the circular bottom cap
    if (bottomRadius != 0):
        angle = 0;
        beginShape(TRIANGLE_FAN);

        # Center point
        vertex(0, tall, 0);
        for i in range(sides + 1):
            vertex(bottomRadius * cos(angle), tall, bottomRadius * sin(angle));
            angle += angleIncrement;
        
        endShape();'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualizes tables of expression data.')
    parser.add_argument('--exp', type=str, dest="expFiles", required=True, nargs="+",
                        help='Input tab-separated files from time series gene expression experiments. One header must be "t" to indicate the time step.')
    parser.add_argument('--sim', type=str, dest="simFiles", required=False, nargs="+",
                        help='Input tab-separated files from time series gene expression simulations. One header must be "t" to indicate the time step.')
    args = parser.parse_args()
    for f in args.expFiles:
        with open(f, 'rb') as infile:
            fileName = os.path.split(f)[1]
            expData[fileName] = {}
            header = None
            timeColumn = None
            for l in infile:
                columns = l.split()
                if len(columns) == 0:
                    continue
                if header == None:
                    header = columns
                    allHeaders = sorted(set(allHeaders).union(header))
                    timeColumn = header.index('t')
                    continue
                t = float(columns[timeColumn])
                minTime = min(t,minTime)
                maxTime = max(t,maxTime)
                expData[fileName][t] = {}
                timeSteps.add(t)
                for i, h in enumerate(header):
                    if i == timeColumn:
                        continue
                    v = float(columns[i])
                    expData[fileName][t][h] = v
                    if not mins.has_key(h):
                        mins[h] = v
                    else:
                        mins[h] = min(v,mins[h])
                    if not maxes.has_key(h):
                        maxes[h] = v
                    else:
                        maxes[h] = max(v,maxes[h])
    if args.simFiles != None:
        for f in args.simFiles:
            with open(f, 'rb') as infile:
                fileName = os.path.split(f)[1]
                simData[fileName] = {}
                header = None
                timeColumn = None
                for l in infile:
                    columns = l.split()
                    if len(columns) == 0:
                        continue
                    if header == None:
                        header = columns
                        allHeaders = sorted(set(allHeaders).union(header))
                        timeColumn = header.index('t')
                        continue
                    t = float(columns[timeColumn])
                    minTime = min(t,minTime)
                    maxTime = max(t,maxTime)
                    simData[fileName][t] = {}
                    timeSteps.add(t)
                    for i, h in enumerate(header):
                        if i == timeColumn:
                            continue
                        v = float(columns[i])
                        simData[fileName][t][h] = v
                        if not mins.has_key(h):
                            mins[h] = v
                        else:
                            mins[h] = min(v,mins[h])
                        if not maxes.has_key(h):
                            maxes[h] = v
                        else:
                            maxes[h] = max(v,maxes[h])
    tspan = (maxTime-minTime)*spanProportion
    t2 = minTime
    t1 = minTime - tspan
        
    allHeaders.remove('t')

    pyprocessing.run()
