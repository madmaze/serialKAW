#!/usr/bin/env python

# Basic imports
import numpy as np
import math
import serial
from threading import Timer 

# Graphing imports
import wx
import matplotlib
matplotlib.use('WXAgg') # do this before importing pylab
from pylab import *

class powerMeter():
	# samples we expect from the arduino
	N_samples = 160
	WaveLength = (74*2)+1 # we want 2 waves to even out random noise.. 149 samples is good enough
	
	# which ADC pins are we talking to?
	VoltSense = 1
	AmpSense = 0
	
	# to calibrate attach no load, set CALIBRATE to True and run for a few mins then fill in below
	VREF = 471.73
	VREF2 = 475.02
	
	# First calibrate VREF (above) then attach a load and view the AMP out put on the display
	# then adjust the CURRENTNORM factor to get the right result
	CURRENTNORM = 0.0057  # conversion to amperes from ADC
	VOLTNORM = 0.476 # conversion to volts from ADC
	
	# Calibration counters
	totalVolt=0.0
	totalAmp=0.0
	tcnt=0
	
	# init data point counter for wattage plotting
	avgwattdataidx=0
	
	def __init__(self, Calibrate=False, plotGraph=True, debug=False, record=True, powerLogFile="test.log"):
		self.CALIBRATE=Calibrate
		self.plotGraph=plotGraph
		self.debug=debug
		self.record=record
		self.dataLog=[]
		self.logFile=powerLogFile

		# average Watt data
		self.avgwattdata = [0] * 1800 # zero out all the data to start
		
		if plotGraph:
			# Setup code mostly borrowed from Adafruit's wattagePlotter.py 
			# Create an animated graph
			self.fig = plt.figure()
			
			# with three subplots: line voltage/current, watts and watthr
			self.wattusage = self.fig.add_subplot(211)
			self.mainswatch = self.fig.add_subplot(212)
			
			# The watt subplot
			self.watt_t = np.arange(0, len(self.avgwattdata), 1)
			self.wattusageline, = self.wattusage.plot(self.watt_t, self.avgwattdata)
			self.wattusage.set_ylabel('Watts')
			self.wattusage.set_ylim(0, 100)
			    
			# the mains voltage and current level subplot
			self.mains_t = np.arange(0, 160, 1)
			self.voltagewatchline, = self.mainswatch.plot(self.mains_t, [0] * 160, color='blue')
			self.mainswatch.set_ylabel('Volts')
			self.mainswatch.set_xlabel('Sample #')
			self.mainswatch.set_ylim(-200, 200)
			
			# make a second axies for amp data
			self.mainsampwatcher = self.mainswatch.twinx()
			self.ampwatchline, = self.mainsampwatcher.plot(self.mains_t, [0] * 160, color='green')
			self.mainsampwatcher.set_ylabel('Amps')
			self.mainsampwatcher.set_ylim(-15, 15)
			
			# and a legend for both of them
			legend((self.voltagewatchline, self.ampwatchline), ('volts', 'amps'))
		
		self.s = serial.Serial(port='/dev/ttyUSB0',baudrate=115200)
		self.s.open()
		
		if plotGraph:
			print "Setting up graphs.."
			timer = wx.Timer(wx.GetApp(), -1)
			timer.Start(250)        # run an in every 'n' milli-seconds
			wx.GetApp().Bind(wx.EVT_TIMER, self.readDataEvent)
			plt.show()
		else:
			self.readData()
	
	def parsePacket(self, packet):
		data = []
		if len(packet)>10 and "\x00" not in packet:
			T = packet.split(";")
			for t in T:
				timestep = []
				readings = t.split(",")
				if len(readings) == 2:
					for s in readings:
						# todo: error checking/handeling 
						if s != "":
							timestep.append(int(s))
					data.append(timestep)
		else:
			print "Skipped packet:",packet
			
		return data
	
	def calibrateADC(self, data):		
		# init empty arrays
		voltagedata = [0] * self.N_samples
		ampdata = [0] * self.N_samples
		
		# populate our data arrays
		for i in range( len(data) ):
			voltagedata[i] = data[i][self.VoltSense]
			ampdata[i] = data[i][self.AmpSense]
		
		for i in range(0, self.WaveLength):
			self.totalVolt += voltagedata[i]
			self.totalAmp += ampdata[i]
			
		self.tcnt += self.WaveLength
		print "VREF:", self.totalVolt / self.tcnt
		print "VREF2:", self.totalAmp / self.tcnt
		
	def processData(self, data):
		# init empty arrays
		voltagedata = [0] * self.N_samples
		ampdata = [0] * self.N_samples
		
		vRMS = 0.0
		aRMS = 0.0
		
		# populate our data arrays
		for i in range( len(data)):
			voltagedata[i] = data[i][self.VoltSense]
			ampdata[i] = data[i][self.AmpSense]
	
		vave = 0.0
		for i in range( len(voltagedata)):
		    # subtract average/remove DC bias
		    voltagedata[i] -= self.VREF2 #ave1/self.WaveLength
		    # scale readings from ADC realm to real values
		    voltagedata[i] *= self.VOLTNORM
		    
		    if i < self.WaveLength:
			    vave += abs(voltagedata[i])
			    # calculate V^2 for RMS
			    vRMS += voltagedata[i]**2
		
		# get peakVoltages
		vmax = max(voltagedata)
		vmin = min(voltagedata)
		
		aave = 0.0
		wattdata = [0] * self.WaveLength
		# normalize current readings to amperes
		for i in range(len(ampdata)):
		    # VREF is the hardcoded 'DC bias' value, its
		    # about 492 but would be nice if we could somehow
		    # get this data once in a while maybe using xbeeAPI
		    ampdata[i] -= self.VREF
		    # the CURRENTNORM is our normalizing constant
		    # that converts the ADC reading to Amperes
		    ampdata[i] *= self.CURRENTNORM
		    
		    if i < self.WaveLength:
			    aave += abs(ampdata[i])
			    aRMS += ampdata[i] ** 2
			    wattdata[i] = ampdata[i] * voltagedata[i]
		###
		# this gives us the mean of the sum of squares
		# then sqrt to get the RMS
		# RMS Amps:
		aRMS /= self.WaveLength
		aRMS = math.sqrt(aRMS)
		# RMS Volts:
		vRMS /= self.WaveLength
		vRMS = math.sqrt(vRMS)
		###
		
		wattAve = 0.0
		for w in wattdata:
			wattAve += w
		wattAve /= len(wattdata)
		
		# Add the current watt usage to our graph history
		self.avgwattdata[self.avgwattdataidx] = wattAve
		self.avgwattdataidx += 1
		
		if (self.avgwattdataidx >= len(self.avgwattdata)):
		    # If we're running out of space, shift the first 10% out
		    tenpercent = int(len(self.avgwattdata)*0.1)
		    for i in range(len(self.avgwattdata) - tenpercent):
			self.avgwattdata[i] = self.avgwattdata[i+tenpercent]
		    for i in range(len(self.avgwattdata) - tenpercent, len(self.avgwattdata)):
			self.avgwattdata[i] = 0
		    self.avgwattdataidx = len(self.avgwattdata) - tenpercent
		    
		if self.plotGraph:
			self.wattusageline.set_ydata(self.avgwattdata)
			self.voltagewatchline.set_ydata(voltagedata)
			self.ampwatchline.set_ydata(ampdata)
		
		# Debug Info
		if self.debug:
			print "\nave Amp(ave/RMS):", aave, aave / self.WaveLength, aRMS
			print "ave Volt:", vave, vave / self.WaveLength, vmin, vmax
			print "rms/trueRMS Volt", vmax / math.sqrt(2), vRMS
			print "ave Watt:", wattAve
		else:
			print "Volt/Amp/Watt:", aRMS, vRMS, wattAve 
		
		if self.record:
			self.recordData(aRMS, vRMS, wattAve)
		
		#if wattAve > 100:
		#	plt.savefig("test.png")
		#	print "I think we may have come across an odd spike.. exiting and saving plot"
		#	exit()
		
		# update Graph
		if self.plotGraph:
			self.fig.canvas.draw()
	
	def recordData(self,aRMS, vRMS, wattAve):
		if self.logFile != "":
			f = open(self.logFile,"a")
			f.write(str(aRMS)+" "+str(vRMS)+" "+str(wattAve)+"\n")
			f.close()
		else:
			self.dataLog.append((aRMS, vRMS, wattAve))
		
	def readDataEvent(self, event):
		self.readData()
			
	def readData(self):
		if self.s.isOpen:
			p = self.s.readline().strip()
			data = self.parsePacket(p)
			if len(data) == self.N_samples:
				if self.CALIBRATE:
					self.calibrateADC(data)
				else:
					self.processData(data)
				
		if self.plotGraph is False:
			Timer(0.25, readData).start()

if __name__ == "__main__":
	meter = powerMeter()
