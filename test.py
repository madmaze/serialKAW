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


# Lets get a powerMeter without the GUI and dont start monitoring immediately
meter = pm.powerMeter(plotGraph=False,powerLogFile="",MonitorOnStart=False, verbose=False)

# testMachine
testHostname = "user@testmachine"
testKeys = "~/.ssh/test"

# path to test on testMachine
testPath = "./Code/Benchmark/test.sh"

# start the monitor and give it time to record a baseline power consumption
meter.startMonitoring()
time.sleep(10)

# run test on remote machine
cmd = "ssh -i " + testKeys + " " + testHostname + " '" + testPath + "'"
#print cmd
run(cmd)

# make sure the test is done then stop monitoring
time.sleep(10)
meter.stopMonitoring()

# Get get the power consumption log 
log = meter.getDataLog()

now = datetime.datetime.now()
nowstr = now.strftime("%Y%m%d_%H%M%S")
curdir = "./logs/"+nowstr
os.mkdir(curdir)

# write out power consumption in CSV
logFile = curdir+"/powerlog.csv"
f = open(logFile,"a")
f.write(testHostname+"\n")
for k in log:
	f.write(k[0]+","+str(k[3])+"\n")
	
f.close()

# copy back test log from testMachines
cmd = "scp -i " + testKeys + " "+testHostname+":~/Code/Benchmark/test.log "+curdir+"/test.log"
#print cmd
run(cmd)


# record power consumption of testMachine at idle
#print "Idle run log"
meter.clearData()
meter.startMonitoring()

#print "logging..."
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
