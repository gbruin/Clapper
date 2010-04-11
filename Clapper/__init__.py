import eg

eg.RegisterPlugin(
	name = "Clapper",
	author = "Garrett Brown",
	version = "0.1",
	kind = "remote",
	description = "Plugin for detecting claps."
)

from threading import Event, Thread
import pyaudio
import math
import struct

class Clapper(eg.PluginBase):
	RATE = 44100
	FORMAT = pyaudio.paInt16
	#FORMAT = pyaudio.paFloat32
	WINDOW = 100 # ms
	THRESHOLD = 5.0 # > equals less probability of false alarm
	
	def __init__(self):
		self.AddAction(Debug)
		self.p = pyaudio.PyAudio()
	
	def __start__(self):
		self.stopThreadEvent = Event()
		self.stream = self.p.open(
			format = self.FORMAT,
			channels = 1,
			rate = self.RATE,
			input = True,
			frames_per_buffer = self.RATE * self.WINDOW / 1000
		)
		thread = Thread(
			target = self.ThreadLoop,
			args = (self.stopThreadEvent, )
		)
		thread.start()
	
	def __stop__(self):
		self.stopThreadEvent.set()
		self.stream.close()
	
	def __del__(self):
		p.terminate()
	
	def ThreadLoop(self, stopThreadEvent):
		output = [0]
		j = 0
		while not stopThreadEvent.isSet():
			j += 1
			#if j == 3:
			#	break
			# Record the microphone data
			data = self.record()
			# Prepend the last frame of filtered data
			data = self.pack(output[len(output)-1]) + data
			# Filter the recorded data
			output = self.BandPass(data, 500, 1500)
			# Compute the power of 1ms samples
			samples = []
			sum = 0
			powerOver1000 = False
			for i in range(0, self.WINDOW * 1): # 1ms samples
				start = int(i * self.RATE / (1000 * 1))
				end = int((i + 1) * self.RATE / (1000 * 1)) - 1
				power = self.RMS(output[start:end])
				samples.append(power)
				sum += power
				if power > 1000:
					powerOver1000 = True
			
			claps = self.DetectClaps(samples, sum)
			
			if powerOver1000:
				output = claps
				event = ""
				for i in range(0, len(output)):
					event += "\t" + str(int(output[i]))
				self.TriggerEvent("Data captured (" + str(j) + "): " + event)
			#stopThreadEvent.wait(5.0)
			# cell-averaging constant false alarm rate detection
	
	def record(self):
		try:
			# Read a window of data
			data = self.stream.read(self.RATE * self.WINDOW / 1000)
		except IOError, e:
			if e[1] == pyaudio.paInputOverflowed:
				print e
			data = '\x00' * (16/8) * 1 * (self.RATE * self.WINDOW / 1000) #value * format_bits * num_channels * frames
		return data
	
	def unpack(self, little, big):
		'Helper function that conbines a little endian byte with its big endian counterpart.'
		t = 256 * ord(big) + ord(little);
		if t > 32768:
			return t - 65536
		return t
	
	def pack(self, value):
		'Opposite of unpack.'
		value = int(value)
		if value < 0:
			value += 65536
		return chr(value % 256) + chr(value / 256)
	
	def BandPass(self, data, highpassFreq, lowpassFreq):
		'''First-order band-pass filter. For a sharper cutoff-frequency corner, an
		   inverse Chebyshev filter or a high-order Butterworth filter should be used.'''
		
		# Calculate the mean to normalize the data
		mean = 0
		for i in range(2, len(data), 2):
			mean += self.unpack(data[i], data[i+1])
		mean = round(float(mean) / (len(data) / 2))
		
		# Calculate discrete-time oscillating parameter (a) and smoothing parameter (b)
		RC_high = 1.0 / (2 * math.pi * highpassFreq)
		RC_low = 1.0 / (2 * math.pi * lowpassFreq)
		dt = 1.0 / self.RATE
		a = RC_high / (RC_high + dt)
		b = dt / (RC_low + dt)
		
		# Filter the data with the passband between highpassFreq and lowpassFreq
		low = high = frame = self.unpack(data[0], data[1])
		output = []
		for i in range(2, len(data), 2):
			prevFrame = frame
			frame = self.unpack(data[i], data[i+1]) - mean
			# High-pass filter, added bonus of getting rid of any DC current in the mic
			high = a * (high + frame - prevFrame)
			# Low-pass filter
			low = b * high + (1-b) * low
			output.append(low)
		return output
	
	def RMS(self, data):
		'Computes the RMS of the data set.'
		s = 0
		#return absMean(data) # Use on slow computers
		for i in data:
			s += i*i
		return math.sqrt(s / len(data))
	
	def absMean(self, data):
		'Computes the absolute average of the data set.'
		s = 0
		for i in data:
			s += abs(i)
		return s / len(data)
	
	def DetectClaps(self, cells, sum):
		'Search for claps using cell-averaged constant false alarm rate detection.'
		maxWidth = 5 # ms
		
		hitArray = []
		for i in range(0, len(cells)):
			# Find the cell-averaged threshold power of non-guard cells
			localPower = localWidth = 0
			for j in range(i - maxWidth/2, i + maxWidth/2):
				if j >= 0 and j < len(cells):
					localPower += cells[j]
					localWidth += 1
			averagePower = self.THRESHOLD * (sum - localPower) / (len(cells) - localWidth)
			hit = cells[i] / (int(averagePower) + 1)
			if hit > 9:
				hit = 9
			hitArray.append(hit)
		return hitArray
		
		


'''
class ClapEvent:
	events = []
	eventsInWindow = []
	
	def addEvent(self, time):
		events.append(self.__Event(time))
	
	def nextWindow():
		if len(self.eventsInWindow) == 0:
			for event in events
				event.
		if len(self.eventsInWindow) == 0
	
	class __Event:
		def __init__(self, time):
			self.t = time
			self.windowAge = 0
'''

class Debug(eg.ActionBase):
	name = "Debug"
	description = "Prints debug information."
	
	def __call__(self):
		print "Hello World!"

\