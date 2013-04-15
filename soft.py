import random, re, os, sys

class softVector:
    timeKeys = [re.compile(r'(?:(?P<hours>\d+)\s*h[ours]*)?\s*\,*(?:(?P<minutes>\d+)\s*m[inutes]*)?\s*\,*(?:(?P<seconds>\d+)\s*s[econds]*)?', re.I)]    # will match strings like '12 min 8SECONDS' or '2 m'
    def __init__(self):
        self.timepoint = None
        self.descriptions = []
        
        self.nextPoint = None
        self.previousPoint = None
        
        self.values = {}
    
    def addDescription(self, d):
        setTimepoint = False
        for r in softVector.timeKeys:
            m = re.match(r,d).groupdict()
            numSeconds = 0
            if m.get('seconds',None) != None:
                numSeconds += float(m['seconds'])
            if m.get('minutes',None) != None:
                numSeconds += float(m['minutes'])*60
            if m.get('hours',None) != None:
                numSeconds += float(m['hours'])*3600
            if m.get('days',None) != None:
                numSeconds += float(m['days'])*86400
            if numSeconds > 0:
                self.timepoint = numSeconds
                setTimepoint = True
                break
        if not setTimepoint:
            self.descriptions.append(d)
    
    def isRelated(self, other):
        # Return true only if either no additional descriptions are shared or ALL descriptions are shared
        for d in self.descriptions:
            if not d in other.descriptions:
                return False
        return True
    
    def __cmp__(self, other):
        if not isinstance(other,softVector) or self.timepoint == None or other.timepoint == None:
            return -1
        else:
            return self.timepoint - other.timepoint
    
class SoftFile:
    def __init__(self, path):
        self.data = {}
        self.genes = []
        self.starts = {}
        
        with open(path,'rb') as infile:
            currentDesc = None
            
            headerOrder = None
            families = []
                        
            for line in infile:
                if line.startswith('!subset_description'):
                    line = line.strip()
                    currentDesc = line[line.find('=')+2:]
                elif line.startswith('!subset_sample_id'):
                    line = line.strip()
                    line = line[line.find('=')+2:]
                    assert currentDesc != None
                    for h in line.split(','):
                        if not self.data.has_key(h):
                            self.data[h] = softVector()
                        self.data[h].addDescription(currentDesc)
                elif len(line) <= 1 or line.startswith('#') or line.startswith('!'):
                    continue
                elif line.startswith('^'):
                    currentDesc = None
                elif headerOrder == None:
                    # Group families of data
                    for hObj in self.data.itervalues():
                        foundFamily = False
                        for members in families:
                            if members[0].isRelated(hObj):
                                members.append(hObj)
                                foundFamily = True
                                break
                        if not foundFamily:
                            families.append([hObj])
                    # Sort and link families
                    for members in families:
                        prevObj = None
                        for hObj in sorted(members):
                            if prevObj != None:
                                hObj.previousPoint = prevObj
                                prevObj.nextPoint = hObj
                            prevObj = hObj
                    headerOrder = line.split()[2:]
                    # Get the starting points for each description
                    for h,hObj in self.data.iteritems():
                        for d in hObj.descriptions:
                            startingPoint = hObj
                            while startingPoint.previousPoint != None:
                                startingPoint = startingPoint.previousPoint
                            if self.starts.has_key(d):
                                assert (self.starts[d].timepoint == None and startingPoint.timepoint == None) or self.starts[d] == startingPoint
                            else:
                                self.starts[d] = startingPoint
                else:
                    columns = line.split()
                    gene = columns[1]
                    if gene == 'EMPTY':
                        continue
                    self.genes.append(gene)
                    for i,h in enumerate(headerOrder):
                        if columns[i+2] != 'null':
                            self.data[h].values[gene] = float(columns[i+2])
        infile.close()
    
    def getVectors(self, attr1, attr2):
        vectors = {}
        for d,hObj in self.starts.iteritems():
            vectors[d] = []
            x = hObj.values.get(attr1)
            y = hObj.values.get(attr2)
            if hObj.nextPoint == None:
                if x != None and y != None:
                    vectors[d].append((x,y,x,y))
            else:
                lastX = x
                lastY = y
                currentObj = hObj
                while currentObj.nextPoint != None:
                    currentObj = currentObj.nextPoint
                    x = currentObj.values.get(attr1)
                    y = currentObj.values.get(attr2)
                    if lastX != None and lastY != None and x != None and y != None:
                        vectors[d].append((lastX,lastY,x,y))
                    lastX = x
                    lastY = y
        return vectors
    
    def geneList(self):
        return list(self.genes)
    
    def classList(self):
        return self.starts.keys()