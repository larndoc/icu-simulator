#plot power spectral density of the sawtooth waveform? 
#plot frequency sprectrum of the sawtooth waveform? 

import serial 
import argparse
import string
import time 
import datetime
import binascii
import logging
import numpy
import statistics
from threading import Thread
import math
import os


#these are the number of bits in the x, y and z coordinates in the fib file.
number_of_bits_coordinates_fib = [24, 24, 24]
number_of_bits_coordinates_fob = [24, 24, 24]


#wrap this inside a function 
def init_debug_logger(): 
	logging.basicConfig(filename='debugger.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	
start_science = True
recieve_serial = True
switch_off = False

def build_config_command_val(): 
	fee_number = (
	"0> FIB \n"
	"1> FOB \n"
	"2> FSC \n"
	)
	print(fee_number)
	cmd = input('> please choose an input: ')	
	cmd_val = (int(cmd, 16)).to_bytes(1, byteorder = 'big')
	read_write = (
	"0) read \n" 
	"1) write \n"
	)
	print(read_write)
	rm_wr = input('> please choose an input: ')
	rm_wr_val = (int(rm_wr, 16)).to_bytes(1, byteorder = 'big')
	
	config_id = input('>please enter config id: ')		
	config_id_val = (int(config_id, 16)).to_bytes(1, byteorder = 'big')
	
	config_val = input('>please enter config val: ')
	choice = (int(config_val, 16).to_bytes(3, byteorder='big'))
	
	print (cmd_val + rm_wr_val + config_id_val + choice )
	return cmd_val + rm_wr_val + config_id_val + choice
	
def build_fee_packet(): 						
	activate_fee = (
	"5) activate_fee \n"
	"6) de-activate fee \n"
	"3) go back to previous menu \n"
	)
	print(activate_fee)
	cmd = input('please choose an input: ')
	cmd_val = (int(cmd, 16).to_bytes(1, byteorder = 'big'))
	print(cmd_val) 
	if(cmd == '3'): 
		return cmd_val
	else:
		interface 	= (
						"0) fib interface \n"
						"1) fob interface \n"
						"2) fsc interface \n"
						)
		print(interface)
		fee_interface = input('please choose an input: ')
		
		#fee_interface = int(nb, base = 16)
		#command = (cmd.to_bytes(1, byteorder = 'big') + fee_interface.to_bytes(1, byteorder = 'big') )
		return (int(cmd, 0)).to_bytes(1, byteorder = 'big') + (int(fee_interface, 0)).to_bytes(1, byteorder = 'big')
	

def debug_information(data): 
	print(binascii.hexlify(data))
	
def minute_tick(current_minutes, old_minutes): 
	if(current_minute != old_minutes): 
		old_minutes  = current_minute
		return True 
	else: 
		return False
		
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
		self.coordinate = ['', '', ''] 
		self.fib_counter = 0 
		self.old_minutes = 0
		self.fob_counter = 0 
		old_minutes = 0 
		self.fsc_counter = 0;
		self.start_science =  False
		self.zeeman_controller = []
		self.mc_controller	   = []
		self.current_time = datetime.datetime.now()
		with open("avg_zeeman.csv", 'w') as self.avg_zeeman_h: 
			self.avg_zeeman_h.write("population mean" + "," + "population standard deveation" + "\n")
		with open("avg_mc.csv", 'w')     as self.avg_mc_controller: 
			self.avg_mc_controller.write("population_mean" + "," + "population standard deveation" + "\n")
		
	def get_bit_rate(self): 
		logging.debug('current bit rate for fsc per second is ' + str(self.fsc_counter * self.total_bytes/60))
		logging.debug('current bit rate for fib per second is ' + str(self.fib_counter * self.total_bytes/60)) 
		logging.debug('current bit rate for fob per second is ' + str(self.fob_counter * self.total_bytes/60)) 
	def update_average_zeeman(self):
			if(len(self.zeeman_controller) != 0):
				with open("avg_zeeman.csv", 'a') as self.avg_zeeman_h: 
					self.avg_zeeman_h.write(str(statistics.mean(self.zeeman_controller)) + "," + str(statistics.stdev(self.zeeman_controller)) + "\n")
					self.zeeman_controller = []
	def update_average_mc_controller(self): 
			if(len(self.mc_controller) != 0): 
				with open("avg_mc.csv", 'a') as self.avg_mc_controller: 
					self.avg_mc_controller.write(str(statistics.mean(self.mc_controller)) + "," + str(statistics.stdev(self.mc_controller)) + "\n")
					self.mc_controller = []

	def update_fsc(self): 
		self.update_average_zeeman()
		self.update_average_mc_controller()
		
	def get_nfib(self): 
		return self.n_fib 
	def get_nfob(self): 
		return self.n_fob 
	def get_nfsc(self): 
		return self.n_fsc 
	
	def update_fib_data_limits(self): 
		self.fib_lower_limit = 8 
		self.fib_upper_limit = self.fib_lower_limit + 10*self.n_fib
	
	def update_fob_data_limits(self): 
		self.fob_lower_limit = self.fib_upper_limit 
		self.fob_upper_limit = self.fob_lower_limit + 10*self.n_fob
	
	def update_fsc_data_limits(self): 
		self.fsc_lower_limit = self.fob_upper_limit 
		self.fsc_upper_limit = self.fsc_lower_limit + 10*self.n_fsc
	
	def update(self):	 
		data = bytearray((self.port).read(size = 8))
		if(data != ''): 
			self.id	= str(data[0])
			self.sync_counter       		= ("{}".format(int.from_bytes(data[1 : 5], byteorder = 'big')));  
			delta_val 						= float(self.sync_counter) * 1/128 
			self.time 						= self.current_time + datetime.timedelta(milliseconds = delta_val*1000);						#3000 milliseconds is the time bias
			self.n_fib 						= (data[5])
			self.n_fob 						= (data[6])
			self.n_fsc 						= (data[7])
			self.fib_counter 				= self.fib_counter + self.n_fib 
			self.fob_counter 				= self.fob_counter + self.n_fob
			self.fsc_counter 				= self.fsc_counter + self.n_fsc
	

			
			#self.fsc_counter = self.fsc_counter + self.n_fsc
			#logging.debug('RECIEVED SCIENCE PACKET (FIB:%3d, FOB:%3d, FSC%3d)', self.n_fib, self.n_fob, self.n_fsc)
			self.update_fib_data_limits()
			self.write_fib()
			self.buffer[0] = ''
			
			
			self.update_fob_data_limits() 
			self.write_fob() 
			self.buffer[1] = ''
			
			self.update_fsc_data_limits()
			self.write_fsc() 
			self.buffer[2] = ''
		
			self.coordinate 				= ['', '', '']
	
	
		
	def write_fsc(self):
		for i in range(0, self.n_fsc):
			self.buffer[2]  = self.port.read(size = 10);
			sensor_temp_controller 			= self.buffer[2][0] & 0xF0
			laser_temp_controller  			= self.buffer[2][0] & 0x0F
			laser_current_controller 		= self.buffer[2][1] & 0xF0 
			microwave_reference_controller 	= self.buffer[2][1] & 0x0F
			zeeman_controller 				= self.buffer[2][2]
			science_data_id 				= self.buffer[2][3]
			science_data_val				= ("{}".format(int.from_bytes(self.buffer[2][4:8], byteorder = 'big')))				
			time_stamp						= ("{}".format(int.from_bytes(self.buffer[2][8:11], byteorder = 'big')))
			self.zeeman_controller.append(zeeman_controller)
			self.mc_controller.append(microwave_reference_controller)
			with open(self.fsc_sci_name + ".csv", 'a') as fsc_handler:
				fsc_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + ",")
				fsc_handler.write(str(sensor_temp_controller) + "," + str(laser_temp_controller) + "," + str(laser_current_controller) + "," + str(microwave_reference_controller) + "," +  str(zeeman_controller) + "," + str(science_data_id) + "," + str(science_data_val) + "," + str(time_stamp) + "\n")
			
	def write_fob(self):
		for i in range(0,self.n_fob) :
			self.buffer[1] = self.port.read(size = 10)
			for i in range(0, 3):
				self.coordinate[i] = ((int.from_bytes( self.buffer[1][3*i + 2 : 3*i], byteorder = 'big' )))
				self.coordinate[i] = self.coordinate[i] - (2**number_of_bits_coordinates_fob[i]) * (self.coordinate[i] >= 2**(number_of_bits_coordinates_fob[i])/2)
			sensor_range = self.buffer[1][9]
			with open(self.fob_sci_name + ".csv", 'a') as fob_handler:
				fob_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + ",")
				fob_handler.write(str(self.coordinate[0]) + "," + str(self.coordinate[1]) + "," + str(self.coordinate[2]) + "," + str(sensor_range) + "," + "\n")
	
	def write_fib(self):
		for i in range(0, self.n_fib): 
			self.buffer[0] = self.port.read(size = 10)
			for i in range(0, 3): 
				self.coordinate[i] = ((int.from_bytes(self.buffer[0][3*i : 3*i + 3], byteorder = 'big')))
				self.coordinate[i] = ((self.coordinate[i]) - (2**number_of_bits_coordinates_fib[i]) * ((self.coordinate[i]) >= 2**(number_of_bits_coordinates_fib[i])/2))
			with open(self.fib_sci_name + ".csv", 'a') as fib_handler: 
				fib_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + ",")
				fib_handler.write(str(self.coordinate[0]) + "," + str(self.coordinate[1]) + "," + str(self.coordinate[2]) + "\n")
		
		
	def update_files(self, absolute_path):
		t = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
		self.start_science = True
		self.current_time = datetime.datetime.now() 
		datetime_files = ["fib_sci_" + t, "fob_sci_" + t, "fsc_sci_" + t]
		self.fib_sci_name = "fib_sci_" + t	
		self.fsc_sci_name = "fsc_sci" + t; 
		self.fob_sci_name = "fob_sci" + t; 
		
		if absolute_path != None: 
			self.fsc_sci_name = absolute_path + '/' + self.fsc_sci_name
			self.fib_sci_name = absolute_path + '/' + self.fib_sci_name
			self.fob_sci_name = absolute_path + '/' + self.fob_sci_name
					
		with open(self.fib_sci_name + ".csv", 'a') as fib_handler, open (self.fob_sci_name + ".csv", 'a') as fob_handler,  open (self.fsc_sci_name + ".csv", 'a') as fsc_handler:
			header = "time"  + ","
			fib_handler.write(header + "status" + "," + "x" + "," + "y" + "," + "z" + "\n")
			fob_handler.write(header + "status" + "," + "x" + "," + "y" + "," + "z" + "\n")
			fsc_handler.write(header + "status" + "," + "sensor temperature controller" + "," + "laser temperature controller" + "," + "laser current controller" + "," + "microwave reference controller" + "," + "zeeman_controller" + "," +  "science_data_id" + "," +  "science_data" + "," + "time_stamp" + "\n" ) 
	
	def run(self):
	# arduino startup time
	#timestamp for each of the filenames
		#time.sleep(1)
		while(self.start_science == False): 
			pass
		self.port.flushInput();
		while self.start_science == True:
			if self.port.in_waiting > 0:
				self.update()

	def update_current_time(self):
		self.curent_time = datetime.datetime.now()
		
if __name__ == '__main__':
		baud_rate = 115200
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		parser.add_argument('--abs_path', dest = 'abs_path', help = "check for absolute directory", type = str)
		args = parser.parse_args()
		s = serial.Serial(args.port, baud_rate, timeout = 0.5)
		init_debug_logger(); 
		science_handler = fee_science_reciever(s)
		science_handler.start(); 
		while not science_handler.is_alive(): 
			pass 

		science_handler.update_current_time(); 
		time.sleep(2)
		
		## needed as arduino needs to come up, do not remove. 
		cmd_menu = ("1) Set Time Command \n"
					 "2) Set Config Command \n"
					 "3) Science Mode \n"
					 "4) Config Mode \n"
					 "5) End the script \n")
		command = ''
		
	
		#continue to stay in the loop until the user wants to exit the script in which case we must end the thread
		while(switch_off == False):  
			print(cmd_menu)
			nb = input('please choose an option: ')
			try: 
				choice = int(nb)
			except ValueError as error_msg: 
				print('unable to parse choice as an integer %s' % error_msg)
				logging.debug(error_msg)
				continue 
			if(nb == '2'): 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big') + build_config_command_val());
			elif(nb == '4'):
				command = ((int(nb, 16).to_bytes(1, byteorder = 'big'))) + build_fee_packet(); 
			elif(nb == '3'):
				science_handler.update_files(parser.parse_args().abs_path)
				science_handler.start_science = True; 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big')) 
			elif(nb == '5'): 
				science_handler.start_science = False
				switch_off = True
			if(nb != '5' and science_handler.is_alive() == True):
					science_handler.port.write(bytes(command));
			print(command)	
		
		#waaiting for the thread to finish executing
		#now we know that we terminated the program
		science_handler.join()
		print("program end")
	

#heat map
#rate of change of x, y and z with respect to time 
#moving averages 
#auto correlation 
#confidence interval 
#power spectral desnity 
#frequency spectrum 

