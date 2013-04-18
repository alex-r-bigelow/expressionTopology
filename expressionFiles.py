import re, os

class SoftVector:
    timeKeys = [re.compile(r'(?:(?P<days>\d+)\s*d[ays]*)?\s*\,*(?:(?P<hours>\d+)\s*h[ours]*)?\s*\,*(?:(?P<minutes>\d+)\s*m[inutes]*)?\s*\,*(?:(?P<seconds>\d+)\s*s[econds]*)?', re.I)]    # will match strings like '12 min 8SECONDS' or '2 m'
    def __init__(self):
        self.timepoint = None
        self.descriptions = []
        
        self.nextPoint = None
        self.previousPoint = None
        
        self.values = {}
    
    def addDescription(self, d):
        setTimepoint = False
        for r in SoftVector.timeKeys:
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
        if not isinstance(other,SoftVector) or self.timepoint == None or other.timepoint == None:
            return -1
        else:
            return self.timepoint - other.timepoint
    
class SoftFile:
    def __init__(self, path):
        self.minTime = None
        self.maxTime = None
        
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
                            self.data[h] = SoftVector()
                        self.data[h].addDescription(currentDesc)
                elif len(line) <= 1 or line.startswith('#') or line.startswith('!'):
                    continue
                elif line.startswith('^'):
                    currentDesc = None
                elif headerOrder == None:
                    # Group families of data, also get min and max times
                    for hObj in self.data.itervalues():
                        if hObj.timepoint != None:
                            if self.minTime == None:
                                self.minTime = hObj.timepoint
                                self.maxTime = hObj.timepoint
                            else:
                                self.minTime = min(hObj.timepoint,self.minTime)
                                self.maxTime = max(hObj.timepoint,self.maxTime)
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
                    columns = line.split('\t')
                    gene = columns[1]
                    if gene == 'EMPTY':
                        continue
                    self.genes.append(gene)
                    for i,h in enumerate(headerOrder):
                        if i+2 >= len(columns):
                            continue
                        value = columns[i+2]
                        try:
                            value = float(value)
                            self.data[h].values[gene] = value
                        except:
                            pass
        infile.close()
    
    def getVectors(self, attr1, attr2):
        vectors = {}
        for d,hObj in self.starts.iteritems():
            vectors[d] = []
            x = hObj.values.get(attr1)
            y = hObj.values.get(attr2)
            t = hObj.timepoint
            if hObj.nextPoint == None:
                if x != None and y != None:
                    vectors[d].append((x,y,t,x,y,t))
            else:
                lastX = x
                lastY = y
                lastT = t
                currentObj = hObj
                while currentObj.nextPoint != None:
                    currentObj = currentObj.nextPoint
                    x = currentObj.values.get(attr1)
                    y = currentObj.values.get(attr2)
                    t = currentObj.timepoint
                    if lastX != None and lastY != None and x != None and y != None:
                        vectors[d].append((lastX,lastY,lastT,x,y,t))
                    lastX = x
                    lastY = y
                    lastT = t
        return vectors
    
    def geneList(self):
        return self.genes
    
    def classList(self):
        return self.starts.keys()
    
    def timeRange(self):
        return (self.minTime,self.maxTime)

class TsdFile:
    '''
    Assumes time points are in seconds, requires 'time' to be the first column header
    '''
    def __init__(self, path):
        self.minTime = None
        self.maxTime = None
        self.classes = [os.path.splitext(os.path.split(path)[1])[0]]  # for .tsd files, there's only one class, so we'll use the file name
        with open(path,'rb') as infile:
            allData = infile.read().strip()
            allData = allData[1:-1].replace(')','') # lose the outer parentheses, closing inner parentheses
            self.rows = allData.split(',(')  # we can split each row by the remaining parenthesis
            self.genes = self.rows[0][1:].replace('"','') # There's one remaining open parenthesis that didn't have a comma before it... but it's in the header, from which we also want to remove the quotes
            self.genes = self.genes.strip().split(',')
            self.genes[0] = 'time'
            self.rows = self.rows[1:]
            for i,r in enumerate(self.rows):
                self.rows[i] = r.split(',')
                for j,c in enumerate(self.rows[i]):
                    self.rows[i][j] = float(c.strip())
                    if j == 0:
                        if self.minTime == None:
                            self.minTime = self.rows[i][j]
                            self.maxTime = self.rows[i][j]
                        else:
                            self.minTime = min(self.minTime,self.rows[i][j])
                            self.maxTime = max(self.maxTime,self.rows[i][j])
        infile.close()
    
    def getVectors(self, attr1, attr2):
        if not attr1 in self.genes or not attr2 in self.genes:
            return {}
        
        diffs = []
        
        c1 = self.genes.index(attr1)
        c2 = self.genes.index(attr2)
        
        lastX = None
        lastY = None
        lastT = None
        for r in self.rows:
            x = r[c1]
            y = r[c2]
            t = r[0]
            if lastX != None and lastY != None and lastT != None:
                diffs.append((lastX,lastY,lastT,x,y,t))
            lastX = x
            lastY = y
            lastT = t
        return {self.classes[0]:diffs}
    
    def geneList(self):
        return self.genes[1:]   # don't include time
    
    def classList(self):
        return self.classes
    
    def timeRange(self):
        return (self.minTime,self.maxTime)

class CsvFile:
    def __init__(self, path):
        pass
    
    def getVectors(self, attr1, attr2):
        pass
    
    def geneList(self):
        pass
    
    def classList(self):
        pass
    
    def timeRange(self):
        return (self.minTime,self.maxTime)

class DatFile:
    def __init__(self, path):
        pass
    
    def getVectors(self, attr1, attr2):
        pass
    
    def geneList(self):
        pass
    
    def classList(self):
        pass
    
    def timeRange(self):
        return (self.minTime,self.maxTime)
