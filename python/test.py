import serial 
import argparse
import string
import time 
import datetime
import binascii
from abc import ABCMeta, abstractmethod

class fee_packet: 
	science_data=['','','']
	def update(self, data):			
		self.data = data
		self.id	= str(data[0])
		self.sync_counter   = ("{}".format(int.from_bytes(data[1 : 5], byteorder = 'big'))); 
		delta_val 			= float(self.sync_counter) * 7.8125 
		self.time =          current_time + datetime.timedelta(milliseconds = delta_val) ;
		self.n_fib 			= data[5]
		self.n_fob 			= data[6]
		self.n_fsc 			= data[7] 
		self.n_lower_limit 	= 8  
		
	def get_nfib(self): 
		return self.n_fib 
	def get_nfob(self): 
		return self.n_fob 
	def get_nfsc(self): 
		return self.n_fsc 
		
	def update_time(self): 
		sync_counter = ("{}".format(int.from_bytes(self.data[1 : 5], byteorder = 'big'))); 
		delta_val = sync_counter * 7.8125 
		return (self.time +datetime.timedelta(milliseconds = delta_val))
		

	#@abstractmethod
	def store_to_pc(self, file): 
		file.write((self.time.strftime("%Y%m%d %H:%M:%S.%f")) + "," +  str(self.id) + "," + str(self.n_fsc) + "," + str(self.n_fob) + "," + str(self.n_fsc) + ",")

class fsc_packet(fee_packet):
	#fsc_packet inherits from fee_packet and therefore it should have the attributes id, data, time, n_fib, n_fob, n_fsc and n_lower_limit 
		
	def __init__(self, data, time): 
		fee_packet.update(self, data)
		self.n_upper_limit					= self.n_lower_limit + data[5]*10 + data[6]*10 + data[7]*10
		self.science_data[2] = bytearray(self.data[self.n_lower_limit : self.n_upper_limit])
		self.__sensor_temp_controller 			= self.science_data[2][0] & 0xF0
		self.__laser_temp_controller  			= self.science_data[2][0] & 0x0F
		self.__laser_current_controller 		= self.science_data[2][1] & 0xF0 
		self.__microwave_reference_controller 	= self.science_data[2][1] & 0x0F
		self.__zeeman_controller 				= self.science_data[2][2]
		self.__science_data_id 					= self.science_data[2][3]
		 
		
		self.__science_data_val  				= ("{}".format(int.from_bytes(fee_packet.science_data[2][4:8], byteorder = 'big')))								
		self.__time_stamp 						= ("{}".format(int.from_bytes(fee_packet.science_data[2][8:11], byteorder = 'big')))
		
	
	def store_to_pc(self, file): 
		if(self.n_fsc > 0):
			fee_packet.store_to_pc(self, file)
			file.write(str(self.__sensor_temp_controller) + "," + str(self.__laser_temp_controller) + "," + str(self.__laser_current_controller) + "," + str(self.__microwave_reference_controller) + "," +  str(self.__zeeman_controller) + "," + str(self.__science_data_id) +  "," + str(self.__science_data_val) + "," +  str(self.__time_stamp) + "\n"); 


class fib_packet(fee_packet):
	def update_xyz(self, data, id, time, n_fib, n_fob, n_fsc, x_hb, x_mb, x_lb, y_hb, y_mb, y_lb, z_hlb, z_mb): 
		self.__x 							=   ("{}".format(int.from_bytes([x_hb, x_mb, x_lb], byteorder = 'little')))
		self.__y 							=   ("{}".format(int.from_bytes([y_hb, y_mb, y_lb], byteorder = 'little')))
		self.__z 							=   ("{}".format(int.from_bytes([z_hlb, z_mb, z_hlb], byteorder = 'little')))
				
	def __init__(self, data, time): 
		fee_packet.update(self, data)
		self.n_upper_limit				= 	self.n_lower_limit + data[5]*10
		self.science_data[0] = bytearray(self.data[self.n_lower_limit : self.n_upper_limit])
		self.update_xyz( data, str(data[0]), str(time), data[5], data[6], data[7], fee_packet.science_data[0][0], fee_packet.science_data[0][1], fee_packet.science_data[0][2], fee_packet.science_data[0][3], fee_packet.science_data[0][4], fee_packet.science_data[0][5], fee_packet.science_data[0][6], fee_packet.science_data[0][7])
		
	def store_to_pc(self, file): 
		if(self.n_fib > 0):
			fee_packet.store_to_pc(self, file)
			file.write(self.__x + "," + self.__y + "," + self.__z + "\n")
			
class fob_packet(fee_packet):
	def update_xyz(self, data, id, time, n_fib, n_fob, n_fsc, x_hb, x_mb, x_lb, y_hb, y_mb, y_lb, z_hb, z_mb, z_lb, sensor_range):
		self.__x 							=   ("{}".format(int.from_bytes([x_hb, x_mb, x_lb], byteorder = 'little')))
		self.__y 							=   ("{}".format(int.from_bytes([y_hb, y_mb, y_lb], byteorder = 'little')))
		self.__z 							=   ("{}".format(int.from_bytes([z_hb, z_mb, z_lb], byteorder = 'little')))
		self.__sensor_range 				= 	sensor_range
	def __init__(self, data, time): 
		fee_packet.update(self, data)
		self.n_upper_limit				= 	self.n_lower_limit + data[5]*10
		self.science_data[1] = bytearray(self.data[self.n_lower_limit : self.n_upper_limit])
		self.update_xyz( data, str(data[0]), str(time), data[5], data[6], data[7], fee_packet.science_data[1][2], fee_packet.science_data[1][1], fee_packet.science_data[1][0], fee_packet.science_data[1][5], fee_packet.science_data[1][4], fee_packet.science_data[1][3], fee_packet.science_data[1][8], fee_packet.science_data[1][7], fee_packet.science_data[1][6], fee_packet.science_data[1][9])
		
	def store_to_pc(self, file): 
		if(self.get_nfob() > 0):
			fee_packet.store_to_pc(self, file)
			file.write(str(self.__x) + "," + str(self.__y) + "," + str(self.__z) + "," + str(self.__sensor_range) + "\n")


def debug_information(data): 
	print(binascii.hexlify(data))
	
	

if __name__ == "__main__":
	#initialization of the baud rate 
	#initialization of the argument parser for the user to enter the desired communication port 
	#initialization of the science data and the x, y and z components from all 3 interfaces 
	#setting up the communication via the usb interface with a timeout of 0.5 seconds 
	#the print function messes with the data that is being printed on the console 
	
	baud_rate = 115200 
	parser = argparse.ArgumentParser();
	parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
	args = parser.parse_args() 
	science_data = [0, 0, 0]
	data = 0
	
	s = serial.Serial(args.port, baud_rate, timeout = 1)
	
	# arduino startup time
	time.sleep(1)

	
	#timestamp for each of the filenames
	t  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
	
	#sending start command to the arduino 
	s.write(b'A')
	s.flush()
	header = "time" + "," + "status" + "," + "n_fib" + "," + "n_fob" + "," + "n_fsc" + ","
	#opening all the 3 files with the time_stamp 
	with open("fib_sci_" + t + ".csv", 'a') as f, open ("fob_sci_" + t + ".csv", 'a') as se,  open ("fsc_sci_" + t + ".csv", 'a') as d:
		f.write(header + "x" + "," + "y" + "," + "z" + "\n")
		d.write(header + "sensor temperature controller" + "," + "laser temperature controller" + "," + "laser current controller" + "," + "microwave reference controller" + "," + "zeeman_controller" + "," +  "science_data_id" + "," +  "science_data" + "," + "time_stamp" + "\n")
		se.write(header + "x" + "," + "y" + "," + "z"  + "," + "sensor range" + "\n")
		current_time = datetime.datetime.now()
		while True:
			try:
				data = bytearray(s.read(size = 28))
				s.flushInput()			#debug_information(data)
				
				fee_pack = fee_packet();
				fee_pack.update(data) 
				#print(fee_pack.get_nfib())
				if(fee_pack.get_nfib() > 0): 
					fee_pack = fib_packet(data, time)
					fee_pack.store_to_pc(f)
				
				if(fee_pack.get_nfob() > 0): 
					fee_pack = fob_packet(data, time)
					fee_pack.store_to_pc(se)
					
				if(fee_pack.get_nfsc() > 0): 
					fee_pack = fsc_packet(data, time) 
					fee_pack.store_to_pc(d)
				
				
				#get the value of sync_counter from data, the value of current_time never changes. 
				#we use the formula, time = current_time(constant) + sync_counter * 7.8125 ms (where sync_counter is the variable)
					
				
			except KeyboardInterrupt:
				break;

			
			
	
	
		
	
	