#!/usr/bin/env python
import time
"""
Experimental code for folding multiple test results
onto one another to get higher confidence in our numbers
"""

dataFolder="../Analysis/Test1"
testlog = open(dataFolder+"/test.log","r")
powerlog = open(dataFolder+"/powerlog.csv","r").readlines()
foldedlog = open(dataFolder+"/folded.csv","w")
totalTime=0
testCnt=0
startTime=""
endTime=""
testsBounds=[]
tests=[]
for l in testlog.readlines():
	if "kernel start time:" in l:
		try:
			startTime = l.strip().split(" ")[4:]
			startTime=time.strptime(" ".join(startTime),"%b %d  %H:%M:%S %Y")
			#print "start:", time.strftime("%d %b %Y %H:%M:%S", startTime)
		except:
			print "error parsing time:", l.strip()
	if "kernel end time:" in l:
		try:
			endTime = l.strip().split(" ")[4:]
			endTime = time.strptime(" ".join(endTime),"%b %d  %H:%M:%S %Y")
			testsBounds.append((startTime,endTime))
			#print "end:", time.strftime("%d %b %Y %H:%M:%S", endTime)
		except:
			print "error parsing time:", l.strip()


for s,e in testsBounds:
	testData=[]
	for l in powerlog:
		if "," in l:
			bits=l.strip().split(",")
			tstamp=time.strptime(bits[0].split(".")[0],"%Y:%m:%d-%H:%M:%S")
			# find start
			if s<=tstamp and e>=tstamp:
				#print time.strftime("%d %b %Y %H:%M:%S",s),time.strftime("%d %b %Y %H:%M:%S",e),time.strftime("%d %b %Y %H:%M:%S",tstamp)
				testData.append(l.strip())
	print len(testData)
	tests.append(((s,e),testData))
	
lines=[]
for t,data in tests:
	for i,l in enumerate(data):
		watt = l.split(",")[1]
		if i < len(lines):
			lines[i]+=","+watt
		else:
			lines.append(watt)

for l in lines:
	foldedlog.write(l+"\n")

