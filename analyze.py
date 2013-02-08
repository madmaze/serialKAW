#!/usr/bin/env python

f = open("test.log","r")
totalTime=0
testCnt=0
for l in f.readlines():
	if "GPU time:" in l:
		#print l.strip()
		try:
			elapsedTime = float(l.split(" ")[2])
			testCnt+=1
			totalTime += elapsedTime
			print elapsedTime
		except:
			print "error parsing time:", l.strip()

print "Average time:", totalTime/testCnt
