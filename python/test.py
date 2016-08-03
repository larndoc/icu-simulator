import serial 
import argparse
import string
import time 
import datetime
import binascii
from abc import ABCMeta, abstractmethod
from threading import Thread
from enum import Enum
def debug_information(data): 
	print(binascii.hexlify(data))
	
	

class fee_science_reciever(Thread): 
	#initialization of the baud rate 
	#initialization of the argument parser for the user to enter the desired communication port 
	#initialization of the science data and the x, y and z components from all 3 interfaces 
	#setting up the communication via the usb interface with a timeout of 0.5 seconds 
	#the print function messes with the data that is being printed on the console 
	#s = serial.Serial('COM4', 115200, timeout = 1)
	buffer				= ['', '', '']
	def __init__(self, serial_port): 
		super(fee_science_reciever, self).__init__()
		self.port = serial_port
		self.receive_serial = True 

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
			sensor_range = self.buffer[1][9]
			self.fob_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fsc) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
			self.fob_handler.write(str(x) + "," + y + "," + z + "," + str(sensor_range) + "," + "\n")
	
	def write_fib(self):
		for i in range(0, self.get_nfib()): 
			self.buffer[0] = self.port.read(size = 10)
			x	=   ("{}".format(int.from_bytes([self.buffer[0][0], self.buffer[0][1], self.buffer[0][2]], byteorder = 'little')))
			y	=   ("{}".format(int.from_bytes([self.buffer[0][3], self.buffer[0][4], self.buffer[0][5]], byteorder = 'little')))
			z	=   ("{}".format(int.from_bytes([self.buffer[0][6], self.buffer[0][7], self.buffer[0][6]], byteorder = 'little')))
			self.fib_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fib) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
			self.fib_handler.write(x + "," + y + "," + z + "\n")
		
	def run(self):
	# arduino startup time
	#timestamp for each of the filenames
		#time.sleep(1)
		t  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
		self.port.flushInput()
	#opening all the 3 files with the time_stamp 
		with open("fib_sci_" + t + ".csv", 'a') as self.fib_handler, open ("fob_sci_" + t + ".csv", 'a') as self.fob_handler,  open ("fsc_sci_" + t + ".csv", 'a') as self.fsc_handler:
			header = "time" + "," + "status" + "," + "n_fib" + "," + "n_fob" + "," + "n_fsc" + ","
			self.fib_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			self.fob_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			self.fsc_handler.write(header + "sensor temperature controller" + "," + "laser temperature controller" + "," + "laser current controller" + "," + "microwave reference controller" + "," + "zeeman_controller" + "," +  "science_data_id" + "," +  "science_data" + "," + "time_stamp" + "\n" )
			current_time = datetime.datetime.now() 
			while self.receive_serial:
				if self.port.in_waiting > 0:
					self.update(current_time)

					
class telecommunication_states(enum):
	science_mode = 1 
	config_mode  = 2 
	default_mode = 0
	
if __name__ == '__main__':
		telecommunication_states states = default_mode;
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		args = parser.parse_args() 
		s = serial.Serial(args.port, 115200, timeout = 1)
		time.sleep(2)
		## needed as arduino needs to come up
		
		myThreadOb1 = fee_science_reciever(s)
		myThreadOb1.start()
		while not myThreadOb1.is_alive():
			pass
		print("Thread started")
		
		s.write(b'A')
		
		print("please choose from the following \n")
		print("1) science mode")
		print("2) config mode")
		nb = input(" ")
		
		#time.sleep(2)
		#s.flushInput()
		
		#myThreadOb1.s.write(b'A')
		#time.sleep(1)
		#waiting for the join to finish 
		##
		## here is all the code that needs to run in the main program
		##
		##
		if(states == default_mode): 
			if(nb == '3'): 
				print('entering science mode')
				s.write(b'3')
				
			if(nb == '4'): 
				print('entering config mode')
				s.write(b'4')
			
			if(nb == '6'):
				print('fee_deactivate')
				s.write(b'6') 
			if(nb == '5'):
				print('fee activate')
				s.write(b'5')
			
			
			elif(nb == '2'): 
				
				states = config_mode
			
			elif(nb == '3'): 
				
				states = science_mode
			else: 
				print('invalid command')
				states = config_mode
		if(nb == '3'):
			print("entering science mode")
			while myThreadOb1.receive_serial:
				nb = input("please enter an input: ")
				if(nb == '5'):
					s.write(b'5')
					myThreadOb1.receive_serial = False
		elif(nb == '4'):
			print("entering config mode")
			s.write(b'4')				#stop sending sync pulses 
			if(nb == ')	
			 
		
		
		
		myThreadOb1.join()
		print("program end")
	
		
	
	