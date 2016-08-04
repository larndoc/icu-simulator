import serial 
import argparse
import string
import time 
import datetime
import binascii
import logging
import numpy
import statistics
from abc import ABCMeta, abstractmethod
from threading import Thread




logging.basicConfig(filename='example.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
start_science = False


def build_config_command_val(): 
			fee_number = (
			"0> FIB \n"
			"1> FOB \n"
			"2> FSC \n"
			)
			print(fee_number)
			cmd = input('> please choose an input: ')
			
			read_write = (
			"0) read \n" 
			"1) write \n"
			)
			print(read_write)
			rm_wr = input('> please choose an input: ')
			
			config_id = input('>please enter config id: ')
			
			config_val = input('>please enter config val: ')
			return cmd + rm_wr + config_id + config_val 
	
def build_fee_packet(): 
							
		activate_fee = (
			"5) activate_fee \n"
			"6) de-activate fee \n"
			"3) go to science mode \n"
		)
		print(activate_fee)
		cmd = input('please choose an input: ')
		if(cmd != '3'):
			interface 	= (
						"1) fib interface \n"
						"2) fob interface \n"
						"3) fsc interface \n"
						)
			print(interface)
			fee_interface = input('please choose an input: ')
		#fee_interface = int(nb, base = 16)
		#command = (cmd.to_bytes(1, byteorder = 'big') + fee_interface.to_bytes(1, byteorder = 'big') )
			return cmd + fee_interface
		else:
			return '3'
	

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
		self.start_science = False
		self.fib_counter = 0; 
		self.fob_counter = 0; 
		self.old_minutes = 0; 
		self.fsc_counter = 0; 
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
		
	def update(self):	
		data = bytearray((self.port).read(size = 8))
		self.id	= str(data[0])
		self.sync_counter       		= ("{}".format(int.from_bytes(data[1 : 5], byteorder = 'big')));  
		delta_val 						= float(self.sync_counter) * 1/128 
		self.time 						= self.current_time + datetime.timedelta(milliseconds = delta_val) ;
		self.n_fib 						= int(data[5])
		print(int(data[5]))
		self.n_fob 						= int(data[6])
		self.n_fsc 						= int(data[7])
		self.total_bytes        		= self.n_fib*10 + self.n_fob*10 + self.n_fsc*10 + 8
		self.fib_counter 				= self.fib_counter + self.n_fib 
		self.fob_counter 				= self.fob_counter + self.n_fob
		self.fsc_counter 				= self.fsc_counter + self.n_fsc
		
		if(self.time.minute != self.old_minutes): 
			self.get_bit_rate();
			#self.update_fsc(); 
			
		#self.fsc_counter = self.fsc_counter + self.n_fsc
		#logging.debug('RECIEVED SCIENCE PACKET (FIB:%3d, FOB:%3d, FSC%3d)', self.n_fib, self.n_fob, self.n_fsc)
		total_data_to_read 			= self.n_fib*10 + self.n_fob*10 + self.n_fsc*10
		self.fib_lower_limit 			= 8  
		self.fib_upper_limit    		= self.fib_lower_limit   + 10*self.n_fib
		self.fob_lower_limit 			= self.fib_upper_limit 
		self.fob_upper_limit			= self.fob_lower_limit + 10*self.n_fob 
		self.fsc_lower_limit 			= self.fob_upper_limit 
		self.fsc_upper_limit 			= self.fsc_lower_limit + 10*self.n_fsc
		self.old_minutes				= self.time.minute
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
			self.zeeman_controller.append(zeeman_controller)
			self.mc_controller.append(microwave_reference_controller)
			self.fsc_handler.write(self.time.strftime("%Y%m%d %H:%M:%S.%f") + "," + str(self.id) + "," + str(self.n_fib) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")
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
		while(self.start_science == False): 
			pass
		t  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
		self.port.flushInput()
	#opening all the 3 files with the time_stamp 
		with open("fib_sci_" + t + ".csv", 'a') as self.fib_handler, open ("fob_sci_" + t + ".csv", 'a') as self.fob_handler,  open ("fsc_sci_" + t + ".csv", 'a') as self.fsc_handler:
			header = "time" + "," + "status" + "," + "n_fib" + "," + "n_fob" + "," + "n_fsc" + ","
			self.fib_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			self.fob_handler.write(header + "x" + "," + "y" + "," + "z" + "\n")
			self.fsc_handler.write(header + "sensor temperature controller" + "," + "laser temperature controller" + "," + "laser current controller" + "," + "microwave reference controller" + "," + "zeeman_controller" + "," +  "science_data_id" + "," +  "science_data" + "," + "time_stamp" + "\n" ) 
			while self.receive_serial:
				if self.port.in_waiting > 0:
					self.update()

	def update_current_time(self):
		self.curent_time = datetime.datetime.now()
	
if __name__ == '__main__':

		baud_rate = 115200
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		args = parser.parse_args() 
		s = serial.Serial(args.port, baud_rate, timeout = 1)
		time.sleep(2)
		## needed as arduino needs to come up
		cmd_menu = ("1) Set Time Command \n"
					 "2) Set Config Command \n"
					 "3) Science Mode \n"
					 "4) Config Mode \n"
					 "5) End the script \n")
		
		
		
		fee_interface = ['1) fib interface', '2) fob interface', '3) fsc interface']
		fee_activate = ['1) fee activate (5)', '2) fee deactivate (6)']
		inputstring = ''
		myThreadOb1 = fee_science_reciever(s)
		myThreadOb1.start()
		while not myThreadOb1.is_alive():
			pass
			
		while(myThreadOb1.receive_serial):
			if(inputstring == 'fee_interface'):  
				command = build_fee_packet();
				myThreadOb1.start_science = True
				print(command)
				encoded = command.encode('utf-8')
				myThreadOb1.port.write(encoded)
				inputstring = ''
			elif (inputstring == ''):
				print(cmd_menu)
				nb = input('please choose an option: ')
				try: 
					choice = int(nb)
				except ValueError as error_msg: 
					print('unable to parse choice as an integer %s' % error_msg)
					logging.debug(error_msg)
					continue 
				if(nb == '2'): 
					command = nb + build_config_command_val();
					encoded = command.encode('utf-8')
					s.write(encoded)
					inputstring = ''
					
				if(nb == '4'):
					command = nb; 
					encoded = command.encode('utf-8')
					s.write(encoded)
					inputstring = 'fee_interface'
				elif(nb == '3'): 
					myThreadOb1.start_science = True; 
					myThreadOb1.update_current_time()
					print('initiating science mode')
					encoded = nb.encode('utf-8')
					s.write(encoded)
				elif(nb == '5'): 
					myThreadOb1.receive_serial = False; 
					break; 
				else: 
					inputstring = ''
			
				encoded = nb.encode('utf-8')
				s.write(encoded)
				
				
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
	
		
	
	
