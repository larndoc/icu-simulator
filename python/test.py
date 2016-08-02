import serial 
import argparse
import string
import time 
import datetime
import binascii
from abc import ABCMeta, abstractmethod
from threading import Thread


class fee_packet: 
	buffer				= ['', '', '']
	def __init__(self, f1, f2, f3, serial_port): 
		self.fib_handler = f1
		self.fob_handler = f2
		self.fsc_handler = f3
		self.port = serial_port
	
	def update(self, current_time):	
		data = bytearray((self.port).read(size = 8))
		self.id	= str(data[0])
		self.sync_counter       = ("{}".format(int.from_bytes(data[1 : 5], byteorder = 'big'))); 
		delta_val 				= float(self.sync_counter) * 7.8125 
		self.time 				= current_time + datetime.timedelta(milliseconds = delta_val) ;
		self.n_fib 				= int(data[5])
		self.n_fob 				= int(data[6])
		self.n_fsc 				= int(data[7])
		total_data_to_read 		= self.n_fib*10 + self.n_fob*10 + self.n_fsc*10
		self.fib_lower_limit 	= 8  
		self.fib_upper_limit    = self.fib_lower_limit   + 10*self.n_fib
		self.fob_lower_limit 	= self.fib_upper_limit 
		self.fob_upper_limit	= self.fob_lower_limit + 10*self.n_fob 
		self.fsc_lower_limit 	= self.fob_upper_limit 
		self.fsc_upper_limit 	= self.fsc_lower_limit + 10*self.n_fsc
		
		self.write_fib()
		self.write_fob()
		self.write_fsc()		
	
	def get_nfib(self): 
		return self.n_fib 
	def get_nfob(self): 
		return self.n_fob 
	def get_nfsc(self): 
		return self.n_fsc 
		
	def write_fsc(self):
		for i in range(0, self.get_nfsc()):
			self.buffer[2]  = self.port.read(size = 10); 
			sensor_temp_controller 			= self.buffer[2][0] & 0xF0
			laser_temp_controller  			= self.buffer[2][0] & 0x0F
			laser_current_controller 		= self.buffer[2][1] & 0xF0 
			microwave_reference_controller 	= self.buffer[2][1] & 0x0F
			zeeman_controller 				= self.buffer[2][2]
			science_data_id 				= self.buffer[2][3]
			science_data_val				= ("{}".format(int.from_bytes(self.buffer[2][4:8], byteorder = 'big')))				
			time_stamp						= ("{}".format(int.from_bytes(self.buffer[2][8:11], byteorder = 'big')))
			self.fsc_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fsc) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
			self.fsc_handler.write(str(sensor_temp_controller) + "," + str(laser_temp_controller) + "," + str(laser_current_controller) + "," + str(microwave_reference_controller) + "," +  str(zeeman_controller) + "," + str(science_data_id) + "," + str(science_data_val) + "," + str(time_stamp) + "\n")
	
	def write_fob(self):
		for i in range(0,self.get_nfob()) :
			self.buffer[1] = self.port.read(size = 10)
			x	=   ("{}".format(int.from_bytes([self.buffer[1][2], self.buffer[1][1], self.buffer[1][0]], byteorder = 'little')))
			y	=   ("{}".format(int.from_bytes([self.buffer[1][5], self.buffer[1][4], self.buffer[1][3]], byteorder = 'little')))
			z	=   ("{}".format(int.from_bytes([self.buffer[1][8], self.buffer[1][7], self.buffer[1][6]], byteorder = 'little')))
			sensor_range = self.science_data[1][9]
			self.fib_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fsc) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
			self.fib_handler.write(x + "," + y + "," + z + "," + sensor_range + "," + "\n")
	
	def write_fib(self):
		for i in range(0, self.get_nfib()): 
			self.buffer[0] = self.port.read(size = 10)
			x	=   ("{}".format(int.from_bytes([self.buffer[0][0], self.buffer[0][1], self.buffer[0][2]], byteorder = 'little')))
			y	=   ("{}".format(int.from_bytes([self.buffer[0][3], self.buffer[0][4], self.buffer[0][5]], byteorder = 'little')))
			z	=   ("{}".format(int.from_bytes([self.buffer[0][6], self.buffer[0][7], self.buffer[0][6]], byteorder = 'little')))
			self.fib_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fib) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
			self.fib_handler.write(x + "," + y + "," + z + "\n")


def debug_information(data): 
	print(binascii.hexlify(data))
	
	

class myThread(Thread): 
	#initialization of the baud rate 
	#initialization of the argument parser for the user to enter the desired communication port 
	#initialization of the science data and the x, y and z components from all 3 interfaces 
	#setting up the communication via the usb interface with a timeout of 0.5 seconds 
	#the print function messes with the data that is being printed on the console 
	#s = serial.Serial('COM4', 115200, timeout = 1)
	def __init__(self, s):
		super(myThread, self).__init__()
		self.s = s
		
		
	def run(self):
	# arduino startup time
	#timestamp for each of the filenames
		#time.sleep(1)
		t  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
		self.s.flushInput
	#opening all the 3 files with the time_stamp 
		with open("fib_sci_" + t + ".csv", 'a') as fib_handler, open ("fob_sci_" + t + ".csv", 'a') as fob_handler,  open ("fsc_sci_" + t + ".csv", 'a') as fsc_handler:
			header = "time" + "," + "status" + "," + "n_fib" + "," + "n_fob" + "," + "n_fsc" + ","
			fee_pack = fee_packet( fib_handler, fob_handler, fsc_handler, self.s)
			fee_pack.fib_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			fee_pack.fob_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			fee_pack.fsc_handler.write(header + "sensor temperature controller" + "," + "laser temperature controller" + "," + "laser current controller" + "," + "microwave reference controller" + "," + "zeeman_controller" + "," +  "science_data_id" + "," +  "science_data" + "," + "time_stamp" + "\n" )
			current_time = datetime.datetime.now() 
			while True:
				fee_pack.update(current_time)

if __name__ == '__main__':
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		args = parser.parse_args() 
		s = serial.Serial(args.port, 115200, timeout = 1)
		myThreadOb1 = myThread(s)
		s.write(b'A')
		time.sleep(2)
		s.flushInput()
		myThreadOb1.start()
		myThreadOb1.s.write(b'A')
		time.sleep(1)	
	
	
		
	
	