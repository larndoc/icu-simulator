import serial 
import argparse
import string
import time 
import datetime
import binascii
import logging
from abc import ABCMeta, abstractmethod
from threading import Thread
from enum import Enum

logging.basicConfig(filename='example.log',format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')



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
		self.sync_counter       		= ("{}".format(int.from_bytes(data[1 : 5], byteorder = 'big'))); 
		logging.warning('RECIEVED SCIENCE PACKET')
		delta_val 				= float(self.sync_counter) * 7.8125 
		self.time 				= current_time + datetime.timedelta(milliseconds = delta_val) ;
		self.n_fib 				= int(data[5])
		self.n_fob 				= int(data[6])
		self.n_fsc 				= int(data[7])
		total_data_to_read 			= self.n_fib*10 + self.n_fob*10 + self.n_fsc*10
		self.fib_lower_limit 			= 8  
		self.fib_upper_limit    		= self.fib_lower_limit   + 10*self.n_fib
		self.fob_lower_limit 			= self.fib_upper_limit 
		self.fob_upper_limit			= self.fob_lower_limit + 10*self.n_fob 
		self.fsc_lower_limit 			= self.fob_upper_limit 
		self.fsc_upper_limit 			= self.fsc_lower_limit + 10*self.n_fsc
		
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

	
if __name__ == '__main__':
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		args = parser.parse_args() 
		s = serial.Serial(args.port, 115200, timeout = 1)
		time.sleep(2)
		## needed as arduino needs to come up
		mb = ['1) Set Time Command', '2) Set Config Command', '3) Science Mode', '4) Config Mode', '5) End the script']
		fee_interface = ['1) fib interface', '2) fob interface', '3) fsc interface']
		fee_activate = ['1) fee activate (5)', '2) fee deactivate (6)']
		inputstring = ''
		myThreadOb1 = fee_science_reciever(s)
		myThreadOb1.start()
		while not myThreadOb1.is_alive():
			pass
			
		while(True):
			if(inputstring == 'fee_interface'): 
				print('50) enable fib') 
				print('51) enabled fob') 
				print ('52) enabled fsc') 
				print ('60) disable fib') 
				print ('61) disable fob') 
				print ('62) disable fsc') 
				
				nb = input('please choose an option: ')
				if(nb == '50'): 
					inputstring = 'fee_interface' 
					print('enabled fib')
				
				elif(nb == '51'):
					inputstring = 'fee_interface'
					print('enabled fob')
				elif(nb == '52'): 
					inputstring = 'fee_interface'
					print ('enabled fsc')
				elif(nb == '60'): 
					inputstring = 'fee_interface'
					print ('disabled fib')
				elif(nb == '61'): 
					inputstring = 'fee_interface'
					print ('disabled fob')
				elif(nb == '62'): 
					inputstring = 'fee_interface' 
					print ('disabled fsc')
				elif(nb == '3'): 
					inputstring = ''
					print ('entering science mode')
				else: 
					print('invalid command')
					inputstring = 'fee_interface'
				encoded = nb.encode('utf-8')
				s.write(encoded)
			elif (inputstring == ''):
				for i in range(0, len(mb)):
					print(mb[i])
				nb = input('please choose an option: ')
				if(nb == '4'):
					inputstring = 'fee_interface'
				elif(nb == '3'): 
					print('initiating science mode')
				elif(nb != '2' or nb != '1' or nb != '5' or nb != '6'): 
					print('invalid command')
					inputstring = ''
				else: 
					inputstring = ''
				
				
		#time.sleep(2)
		#s.flushInput()
		
		#myThreadOb1.s.write(b'A')
		#time.sleep(1)
		#waiting for the join to finish 
		##
		## here is all the code that needs to run in the main program
		##
		##

			 
		
		
		
		myThreadOb1.join()
		print("program end")
	
		
	
	
