#!/usr/bin/env python
import serial

import wx
import numpy as np
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
	
def findPeaks(data):
	N_samples=160
	VoltSense=1
	AmpSense=0
	window=[]
	foundPeaks=[]
	for i in range(len(data)):
		window.append(data[i][VoltSense])
		if len(window) > 5:
			window.pop(0)
		if len(window) == 5:
			if window[0] < window[2] and window[1] <= window[2]:
				#print "found uphill"
				if window[2] >= window[3] and window[2] > window[4]:
					#print "found peak:",window,i-2
					foundPeaks.append((window,i-2))
	print "found %s peaks" % (len(foundPeaks))
	
	realPeaks=[]
	# collapse adjacent peaks ie 10,11,48 => 10,48
	# we choose the first of each pair
	for i in range(len(foundPeaks)):
		if i < len(foundPeaks)-1 and foundPeaks[i][1] == foundPeaks[i+1][1]-1:
			realPeaks.append(foundPeaks[i][1])
		elif i < len(foundPeaks)-1 and i == 0 and foundPeaks[i][1] != foundPeaks[i+1][1]-1:
			realPeaks.append(foundPeaks[i][1])
		elif i > 0 and foundPeaks[i-1][1] != foundPeaks[i][1]-1:
			realPeaks.append(foundPeaks[i][1])

	
	if len(realPeaks) != 2:
		if len(foundPeaks) >= 3:
			print "Interesting.. do we have triple readings?"
			print foundPeaks
			print realPeaks
		else:
			print ">>failed to identify peaks", len(foundPeaks)
			print data
			
		return []
	else:
		return realPeaks
			
totalVolt=0.0
totalAmp=0.0
tcnt=0

def graphIt(data):
	N_samples = 160
	WaveLength = (74*2)+1 # we want 2 waves
	VoltSense = 1
	AmpSense = 0
	MAINSVPP = 170 * 2     # +-170V is what 120Vrms ends up being (= 120*2sqrt(2))
	#MAINSVPP = 323     # +-170V is what 120Vrms ends up being (= 120*2sqrt(2))
	# to calibrate attach no load, set CURRENTNORM to 1 and run average for a few mins
	VREF = 470.97
	VREF2 = 474.2
	# to calibrate, first calibrate VREF then attach a load and view the AMP out put on the display
	# then adjust the CURRENTNORM factor to get the right result
	CURRENTNORM = 158  # conversion to amperes from ADC
	VOLTNORM = .508
	
	fig.canvas.draw()
	
	# init empty arrays
	voltagedata=[0]*N_samples
	ampdata=[0]*N_samples
	
	# populate our data arrays
	for i in range(len(data)):
		voltagedata[i]=data[i][VoltSense]
		ampdata[i]=data[i][AmpSense]
		
	# get max and min voltage and normalize the curve to '0'
        # to make the graph 'AC coupled' / signed
        min_v = 1024     # XBee ADC is 10 bits, so max value is 1023
        max_v = 0
        for i in range(len(voltagedata)):
            if (min_v > voltagedata[i]):
                min_v = voltagedata[i]
            if (max_v < voltagedata[i]):
                max_v = voltagedata[i]

        # figure out the 'average' of the max and min readings
        avgv = (max_v + min_v) / 2
        # also calculate the peak to peak measurements
        vpp =  max_v-min_v
        print "VPP:",vpp
        
        # find peaks to get averages from
        #peaks = findPeaks(data)
        
        ave1=0.0
        ave2=0.0
        q=0
        for i in range(0,WaveLength):
        	ave1 += voltagedata[i]
        	ave2 += ampdata[i]
        	q+=1
        	
        print "V/A>>>>>>>>>>", ave1/q, ave2/q, q

	vave=0.0

        vmax=0
        vmin=1024
        for i in range(len(voltagedata)):
            #remove 'dc bias', which we call the average read
            #voltagedata[i] -= avgv
            # We know that the mains voltage is 120Vrms = +-170Vpp
            #voltagedata[i] = (voltagedata[i] * MAINSVPP) / vpp
            voltagedata[i] -= ave1/q
            voltagedata[i] *= VOLTNORM
            #voltagedata[i] /= 2
            if i < 149:
            	    vave+=abs(voltagedata[i])
            if (vmin > voltagedata[i]):
                vmin = voltagedata[i]
            if (vmax < voltagedata[i]):
                vmax = voltagedata[i]
        
        aave=0.0
        #aave2=0.0
        # normalize current readings to amperes
        for i in range(len(ampdata)):
            
            # VREF is the hardcoded 'DC bias' value, its
            # about 492 but would be nice if we could somehow
            # get this data once in a while maybe using xbeeAPI
            ampdata[i] -= VREF
            # the CURRENTNORM is our normalizing constant
            # that converts the ADC reading to Amperes
            ampdata[i] /= CURRENTNORM
            if i < 149:
            	    aave+=abs(ampdata[i])
            #aave2+=ampdata[i]
            
	wattusageline.set_ydata(avgwattdata)
        voltagewatchline.set_ydata(voltagedata)
        ampwatchline.set_ydata(ampdata)
        
	
        #if peaks != [] and (peaks[1]- peaks[0]) == 74:
	print "ave Amp:", aave, aave/149
	print "ave Volt:", vave, vave/149, vmin, vmax
	print vmax/sqrt(2)
	#total+=abs(ave2/(peaks[1]- peaks[0]))
	#tcnt+=1
        	
        #print "ave Volt:", vave, vave/len(ampdata)
        #print "aave2:",aave2/len(ampdata)
        
def readData(event):
	global totalVolt
        global totalAmp
	global tcnt
        if s.isOpen:
		p = s.readline().strip()
		data = parsePacket(p)
		if data != []:
			graphIt(data)
			#print ">>>>>>>>>>>>Rolling average",totalVolt/tcnt, totalAmp/tcnt
		
# Create an animated graph
#fig = plt.figure()
# with three subplots: line voltage/current, watts and watthr
#wattusage = fig.add_subplot(211)
#mainswatch = fig.add_subplot(212)

# Create an animated graph
fig = plt.figure()
# with three subplots: line voltage/current, watts and watthr
wattusage = fig.add_subplot(211)
mainswatch = fig.add_subplot(212)

# data that we keep track of, the average watt usage as sent in
avgwattdata = [0] * 1800 # zero out all the data to start
avgwattdataidx = 0 # which point in the array we're entering new data

# The watt subplot
watt_t = np.arange(0, len(avgwattdata), 1)
wattusageline, = wattusage.plot(watt_t, avgwattdata)
wattusage.set_ylabel('Watts')
wattusage.set_ylim(0, 500)
    
# the mains voltage and current level subplot
mains_t = np.arange(0, 160, 1)
voltagewatchline, = mainswatch.plot(mains_t, [0] * 160, color='blue')
mainswatch.set_ylabel('Volts')
mainswatch.set_xlabel('Sample #')
mainswatch.set_ylim(-200, 200)
#mainswatch.set_ylim(100, 850)

# make a second axies for amp data
mainsampwatcher = mainswatch.twinx()
ampwatchline, = mainsampwatcher.plot(mains_t, [0] * 160, color='green')
mainsampwatcher.set_ylabel('Amps')
mainsampwatcher.set_ylim(-15, 15)
#mainsampwatcher.set_ylim(100, 800)

# and a legend for both of them
legend((voltagewatchline, ampwatchline), ('volts', 'amps'))

s = serial.Serial(port='/dev/ttyUSB0',baudrate=115200)
s.open()

timer = wx.Timer(wx.GetApp(), -1)
timer.Start(250)        # run an in every 'n' milli-seconds
wx.GetApp().Bind(wx.EVT_TIMER, readData)
plt.show()

'''while s.isOpen:
	p = s.readline().strip()
	data = parsePacket(p)
	if data != []:
		graphIt(data)
		'''
