#!/usr/bin/env python
import os, random, shutil

nFiles = 20
dt = 5
tn = 100
columns = ['t','cI','cII','TetR','LacI']
startValues = [0,10,20,1,100]
values = None

shutil.rmtree('results')
os.mkdir('results')
for f in xrange(nFiles):
    with open('results/%i.csv' % (f+1),'wb') as outfile:
        outfile.write('\t'.join(columns) + '\n')
        values = list(startValues)
        while values[0] <= tn:
            outfile.write('\t'.join(str(v) for v in values) + '\n')
            values[0] += dt
            for i,v in enumerate(values[1:]):
                values[i+1] += v*(random.random()-0.5)*0.1
        outfile.close()