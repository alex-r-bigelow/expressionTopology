import random

class SoftFile:
    CLASSES = ['a','b','c']
    def __init__(self, path):
        with open(path,'rb') as infile:
            for line in infile:
                pass
        infile.close()
        self.geneList = ['gene1','gene2','mygene3']
    
    def getVectors(self, attr1, attr2):
        vectors = {}
        lastx = 0
        lasty = 0
        for x in xrange(10):
            for y in xrange(10):
                newX = random.random()
                newY = random.randint(-10,10)
                vectors[random.choice(SoftFile.CLASSES)] = (lastx,lasty,lastx+newX,lasty+newY)
                lastx += newX
                lasty += newY
        return vectors