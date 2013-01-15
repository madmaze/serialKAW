#!/usr/bin/env python

# Misc imports
import numpy as np
import math
import serial
from threading import Timer 


# Globals.. still needed?	
totalVolt=0.0
totalAmp=0.0
tcnt=0
avgwattdataidx=0
plotGraph=True

if plotGraph:
	# GRAPHING imports
	import wx
	import matplotlib
	matplotlib.use('WXAgg') # do this before importing pylab
	from pylab import *

def parsePacket(packet):
	data=[]
	if len(packet)>10 and "\x00" not in packet:
		T = packet.split(";")
		for t in T:
			timestep=[]
			readings = t.split(",")
			#print readings
			if len(readings) == 2:
				for s in readings:
					# todo: error checking/handeling 
					if s != "":
						timestep.append(int(s))
				data.append(timestep)
	else:
		print "Skipped packet:",packet
		
	return data
	
def processData(data):
	N_samples = 160
	WaveLength = (74*2)+1 # we want 2 waves to even out random noise.. 149 samples is good
	VoltSense = 1
	AmpSense = 0
	# to calibrate attach no load, set CURRENTNORM to 1 and run average for a few mins
	VREF = 470.97
	VREF2 = 474.2
	# to calibrate, first calibrate VREF then attach a load and view the AMP out put on the display
	# then adjust the CURRENTNORM factor to get the right result
	CURRENTNORM = 0.00578  # conversion to amperes from ADC
	VOLTNORM = 0.479 # conversion to volts from ADC
	
	if plotGraph:
		fig.canvas.draw()
	
	# init empty arrays
	voltagedata=[0]*N_samples
	ampdata=[0]*N_samples
	vRMS=0.0
	aRMS=0.0
	
	# populate our data arrays
	for i in range(len(data)):
		voltagedata[i]=data[i][VoltSense]
		ampdata[i]=data[i][AmpSense]
        
        # find peaks to get averages from
        ave1=0.0
        ave2=0.0
        for i in range(0,WaveLength):
        	ave1 += voltagedata[i]
        	ave2 += ampdata[i]
        	
        #print "V/A>>>>>>>>>>", ave1/WaveLength, ave2/WaveLength, WaveLength

	vave=0.0
        for i in range(len(voltagedata)):
            # subtract average/remove DC bias
            voltagedata[i] -= ave1/WaveLength
            # scale readings from ADC realm to real values
            voltagedata[i] *= VOLTNORM
            if i < 149:
            	    vave+=abs(voltagedata[i])
            	    # calculate V^2 for RMS
            	    vRMS+=voltagedata[i]**2
        
        # get peakVoltages
	vmax = max(voltagedata)
	vmin = min(voltagedata)
	
        #this gives us the mean of the sum of squares
        # then sqrt to get the RMS
        vRMS /= 149
        vRMS = math.sqrt(vRMS)
        
        aave=0.0
        wattdata=[0] * 149
        # normalize current readings to amperes
        for i in range(len(ampdata)):
            
            # VREF is the hardcoded 'DC bias' value, its
            # about 492 but would be nice if we could somehow
            # get this data once in a while maybe using xbeeAPI
            ampdata[i] -= VREF
            # the CURRENTNORM is our normalizing constant
            # that converts the ADC reading to Amperes
            ampdata[i] *= CURRENTNORM
            if i < 149:
            	    aave+=abs(ampdata[i])
            	    aRMS+=ampdata[i]**2
            	    wattdata[i] = ampdata[i] * voltagedata[i]
        ###
        # this gives us the mean of the sum of squares
        # then sqrt to get the RMS
        # RMS Amps:
        aRMS /= 149
        aRMS = math.sqrt(aRMS)
        # RMS Volts:
        vRMS /= 149
        vRMS = math.sqrt(vRMS)
        ###
        
        wattAve=0.0
        for w in wattdata:
        	wattAve+=w
        wattAve /= len(wattdata)
        
        global avgwattdataidx
        # Add the current watt usage to our graph history
        avgwattdata[avgwattdataidx] = wattAve
        avgwattdataidx += 1
        if (avgwattdataidx >= len(avgwattdata)):
            # If we're running out of space, shift the first 10% out
            tenpercent = int(len(avgwattdata)*0.1)
            for i in range(len(avgwattdata) - tenpercent):
                avgwattdata[i] = avgwattdata[i+tenpercent]
            for i in range(len(avgwattdata) - tenpercent, len(avgwattdata)):
                avgwattdata[i] = 0
            avgwattdataidx = len(avgwattdata) - tenpercent
            
        if plotGraph:
		wattusageline.set_ydata(avgwattdata)
		voltagewatchline.set_ydata(voltagedata)
		ampwatchline.set_ydata(ampdata)
        
        # Debug Info
	print "\nave Amp(ave/RMS):", aave, aave/149, aRMS
	print "ave Volt:", vave, vave/149, vmin, vmax
	print "rms/trueRMS Volt", vmax/math.sqrt(2), vRMS
	print "ave Watt:", wattAve
	if wattAve > 100:
		plt.savefig("test.png")
		print "I think we may have come across an odd spike.. exiting and saving plot"
		exit()
        
def readDataEvent(event):
	readData()
		
def readData():
	global totalVolt
        global totalAmp
	global tcnt
        if s.isOpen:
		p = s.readline().strip()
		data = parsePacket(p)
		if data != []:
			processData(data)
			
	if plotGraph is False:
		Timer(0.25,readData).start()

# average Watt data
avgwattdata = [0] * 1800 # zero out all the data to start

if plotGraph:
	# Setup code mostly borrowed from Adafruit's wattagePlotter.py 
	# Create an animated graph
	fig = plt.figure()
	
	# with three subplots: line voltage/current, watts and watthr
	wattusage = fig.add_subplot(211)
	mainswatch = fig.add_subplot(212)
	
	avgwattdataidx = 0 # which point in the array we're entering new data
	
	# The watt subplot
	watt_t = np.arange(0, len(avgwattdata), 1)
	wattusageline, = wattusage.plot(watt_t, avgwattdata)
	wattusage.set_ylabel('Watts')
	wattusage.set_ylim(0, 100)
	    
	# the mains voltage and current level subplot
	mains_t = np.arange(0, 160, 1)
	voltagewatchline, = mainswatch.plot(mains_t, [0] * 160, color='blue')
	mainswatch.set_ylabel('Volts')
	mainswatch.set_xlabel('Sample #')
	mainswatch.set_ylim(-200, 200)
	
	# make a second axies for amp data
	mainsampwatcher = mainswatch.twinx()
	ampwatchline, = mainsampwatcher.plot(mains_t, [0] * 160, color='green')
	mainsampwatcher.set_ylabel('Amps')
	mainsampwatcher.set_ylim(-15, 15)
	
	# and a legend for both of them
	legend((voltagewatchline, ampwatchline), ('volts', 'amps'))

s = serial.Serial(port='/dev/ttyUSB0',baudrate=115200)
s.open()

if plotGraph:
	print "Setting up graphs.."
	timer = wx.Timer(wx.GetApp(), -1)
	timer.Start(250)        # run an in every 'n' milli-seconds
	wx.GetApp().Bind(wx.EVT_TIMER, readDataEvent)
	plt.show()
else:
	readData()
