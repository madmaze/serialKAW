#!/usr/bin/env python

import powerMeterDaemon as pm
import time
import datetime
import os


def run(cmd):
	f=os.popen(cmd)
	buf=""
	for i in f.readlines():
		buf+=i
	return buf.strip()


meter = pm.powerMeter(plotGraph=False,powerLogFile="",MonitorOnStart=False, verbose=False)
testHostname="ubuntu@carma.pha.jhu.edu"
#testHostname="madmaze@128.220.147.219"
#testHostname="madmaze@128.220.147.143"
testPath="./Code/Benchmark/test.sh"
meter.startMonitoring()
time.sleep(10)
cmd = "ssh -i /home/madmaze/.ssh/tesla "+testHostname+" '"+testPath+"'"
print cmd
run(cmd)
time.sleep(10)
meter.stopMonitoring()
log = meter.getDataLog()
#print log
now=datetime.datetime.now()
nowstr=now.strftime("%Y%m%d_%H%M%S")
curdir="./logs/"+nowstr
os.mkdir(curdir)

logFile = curdir+"/powerlog.csv"

f = open(logFile,"a")
f.write(testHostname+"\n")
for k in log:
	f.write(k[0]+","+str(k[3])+"\n")
	
f.close()

cmd = "scp -i /home/madmaze/.ssh/tesla "+testHostname+":~/Code/Benchmark/test.log "+curdir+"/test.log"
print cmd
run(cmd)


print "Idle run log"
meter.clearData()
meter.startMonitoring()
print "logging..."
time.sleep(130)
meter.stopMonitoring()
log = meter.getDataLog()
logFile = curdir+"/idlePowerlog.csv"

f = open(logFile,"a")
f.write(testHostname+"\n")
for k in log:
	f.write(k[0]+","+str(k[3])+"\n")
	
f.close()
print "all done.."
