#!/usr/bin/env python
import numpy as np
"""
Prints out basic statistics of a power log
"""
f = open("../Analysis/Board2/test.log","r")
totalTime=0
testCnt=0
times=[]
for l in f.readlines():
	if "GPU time:" in l:
		#print l.strip()
		try:
			elapsedTime = float(l.split(" ")[2])
			testCnt+=1
			totalTime += elapsedTime
			times.append(elapsedTime)
			print elapsedTime
		except:
			print "error parsing time:", l.strip()

print "Average time:", totalTime/testCnt
print "StDev:", np.std(times)
print "Mean/Coef of Var", np.mean(times), np.std(times)/np.mean(times), 100*(np.std(times)/np.mean(times)), "%"
