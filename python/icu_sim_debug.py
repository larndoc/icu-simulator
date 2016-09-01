# TODO
# put descriptions for functions and classes

import serial
import argparse
import logging
import time
import binascii
import os
from threading import Thread

def tokenize(string, length, delimter=" "):
	"""add whitespace after 
	every byte in the data-
	stream - default delimiter
	is set to ' ' - skip the 
	first two characters which 
	are " b' " and the last 
	character which is  ' 
    """
	
	return delimter.join(string[i:i+length] for i in range(2,len(string)-1,length)) + "\n"

def build_config_command_val():
	"""the function is triggered 
	only if the user chooses 
	set config command option
	in the main, the user is 
	given a set of options which
	specify: 
    a)to which FEE does the user want to communicate with
	b)read or write command
	c)config id 
	d)config_param_val 
	the try catch block deals with bad data"""
	
	try:
		fee_number 	= ("0> FIB \n" 	"1> FOB \n" "2> FSC \n")
		print(fee_number)
		fee_interface = input('please choose an input: ')	
		cmd_val = int(fee_interface, 0).to_bytes(1, byteorder = 'big')
		read_write = ("0) read \n" 	"1) write \n")
		print(read_write)
		rm_wr = input('> please choose an input: ')
		rm_wr_val = int(rm_wr, 0).to_bytes(1, byteorder = 'big')
		config_id = input('>please enter config id: ')		
		config_id_val = int(config_id, 0).to_bytes(1, byteorder = 'big')
		config_val = input('>please enter config val: ')
		choice = int(config_val, 0).to_bytes(3, byteorder='big')
		return cmd_val + rm_wr_val + config_id_val + choice
	except: 
		print('could not build config command - you will not able to write the following command to the arduino %s' % error_msg)
		logging.debug(error_msg)
	
def build_fee_packet(): 	
	"""the function is only triggered 
	only if the user enters '5' or '6' 
	and wishes to activate/deactivate 
	an fee. the user is given a set of
	options to choose from which indicate 
	which fee does he want to enable/disable, 
	try catch block to deal with malformed input"""
	
	try:
		fee_number 	= ("0> FIB \n" "1> FOB \n" "2> FSC \n")
		print(fee_number)
		fee_interface = input('please choose an input: ')
		fee_interface_val = int(fee_interface, 0).to_bytes(1, byteorder = 'big')
		return fee_interface_val 
	except: 
		print('could not build fee packet - you will not able to write the following command to the arduino %s' % error_msg)
		logging.debug(error_msg)

class hk_interpreter: 	
	"""the class deals with extracting 
	the house keeping data_stream 
	and depositing it in the hk.log 
	file - we initialize the object 
	with the serial port which we 
	configure in the packet_handler class,
	using this port we extract a total of 133 bytes 
	and append b'\x00' at the start of the stream 
	to indicate that it is a house keeping packet - 
	we also check to see if we do recieve the 
	number of packets indicated by the first two 
	bytes in the stream"""
	def __init__(self, port): 
		self.__port = port
	def update(self, size):
		size_t = int.from_bytes(size,byteorder = 'big', signed = False) #this is the true size of the packet excluding the first two bytes that represent the size of the packet 
		counter = self.__port.read(size = 4)
		data = self.__port.read(size = 129)
		data_stream = b'\x00' + counter + data
		if size_t != len(data_stream):
			logging.info('house_keeping_packet malformed!')
			if len(counter) is not 4:
				logging.info('could not read counter')
			elif len(data) is not 129: 
				logging.info('could not read data')
		else: 
			logging.info('recieved house_keeping packet, status OK')
		#we still want to se the contents of the malformed packet
		return str(binascii.hexlify(data_stream))
		 	 
class arduino_due():
	"""the class is used to initialize the
	port which is used by the rest of the 
	classes respectively - includes methods 
	write and read which is there to indicate 
	write commands to the arduino due 
	and read commands recieved from the arduino due"""
	def __init__(self, port): 
		#a baud rate of 115200 bits per second and timeout of None
		self.__port = serial.Serial(port, 115200, timeout = None)
		#arduino initialisation tme
		time.sleep(1)
		# any other initialisation
		
	def write(self, data): 
		"""wrapper function for writing bytes to the arduino due"""
		self.__port.write(bytes(data))
		
	def read(self):
		"""wrapper function for reading bytes sent by the arduino due"""
		return self.__port.read()

	def get_port(self):
		"""getter function to extract the arduino_due port"""
		return self.__port
		

		 
class packet_handler(Thread):
	"""the class primarily serves 
	to multiplex the data into 
	the files hk.txt and sci.txt with 
	the appropiate labels, 
	depending on the first byte 
	recieved the classes sci_interpreter
	and hk_interpreter derive the remaining 
	data stream and return this to the 
	packet_handler
	"""
	#recieves a packet and reads the first byte 
	__filename   = dict()
	__active = True
	def close_connection(self):
		#indicates that we want the thread to terminate
		self.__active = False; 
	
	def __init__(self, port, logdir, sci_filename, hk_filename):
		super(packet_handler, self).__init__()
		self.__port = port
		self.__filename["hk"] = hk_filename
		self.__filename["sci"] = sci_filename
		if logdir is None: 
			logdir = "data"
		else: 
			logdir = logdir.rstrip("/")
		if os.path.exists(logdir): 
			for key, value in self.__filename.items(): 
				self.__filename[key] = logdir + "/" + value
		else: 
			#the directory doesn't exist! 
			raise SystemExit('not a valid directory')

		self._pyserial_hack = False
		try:
			self.__port.in_waiting
		except:
			self._pyserial_hack = True

	def __in_waiting(self):
		"""ensures that that the in_waiting function works for versions of python 3.0 or greater"""
		if(self._pyserial_hack):
			return self.__port.inWaiting()
		else:
			return self.__port.in_waiting

		
	def run(self):
		self.__port.flushInput()
		s = sci_interpreter(self.__port)
		h = hk_interpreter(self.__port)
		##everytime we execute the script we overwrite the files if they already exist
		with open(self.__filename['hk'], 'w') as f_hk, open(self.__filename['sci'], 'w') as f_sci:
			f_sci.write('status time_3 time_2 time_1 time_0 n_fib n_fob n_fsc' + "\n")
			header = [] 
			header.append("status time_3 time_2 time_1 time_0") 
			header.append(" ".join(["pcu"+str(v) for v in range(31,-1,-1)]))
			header.append(" ".join(["fib"+str(v) for v in range(39,-1,-1)]))
			header.append(" ".join(["fob"+str(v) for v in range(3,-1,-1)]))
			header.append(" ".join(["fsc"+str(v) for v in range(51,-1,-1)]))
			f_hk.write("{}\n".format(" ".join(header))) 
			while self.__active:
				if (self.__in_waiting() > 2):
					size = self.__port.read(size = 2)
					decision_hk_sci = self.__port.read(size = 1)
					#we have recieved a byte that indicates whether it is a science or a house keeping packet 
					if len(decision_hk_sci) > 0:
						if decision_hk_sci[0] == 0:  
							#2 indicates that we want the delimiter after every 2 HEX characters in our data stream
							f_hk.write(tokenize(h.update(size), 2))
							
							#empty the contents of the f_hk buffer
							f_hk.flush()
						elif decision_hk_sci[0] == 1: 
							#2 indicates that we want the delimiter after every 2 HEX characters in our data stream
							f_sci.write(tokenize(s.update(size), 2))
							
							#empty the contents of the f_sci buffer 
							f_sci.flush()
							
class sci_interpreter():
		def __init__(self, port): 
			self.__port = port
			self.total_count = 0
		def update(self, size):	
			size = int.from_bytes(size ,byteorder = 'big', signed = False)
			counter = self.__port.read(size = 4)
			n_fee = self.__port.read(size = 3)
			
			self.total_count += n_fee[0] + n_fee[1] + n_fee[2] 
			logging.info('n_total %s n_fib %s, n_fob %s, n_fsc %s', self.total_count, n_fee[0], n_fee[1], n_fee[2])
			
			data_stream = b'\x01' + counter + n_fee
			
			for i in range(0, n_fee[0]): 
				data_stream += self.__port.read(size = 10) 			
			for i in range(0, n_fee[1]): 
				data_stream += self.__port.read(size = 10)
			for i in range(0, n_fee[2]):
				data_stream += self.__port.read(size = 11)
			if size != len(data_stream): 
				print('sci packet malformed!')
				logging.info('sci packet malformed!')
				if len(counter) is not 4: 
					logging.info('could not read counter')
				if len(n_fee) is not 3: 
					logging.info('could not read n_fee')
				else: 
					logging.info('could not read data')
			else: 
					logging.info('recieved science_packet, status OK')
			return str(binascii.hexlify(data_stream)) 
			
if __name__ == '__main__':
		hk_filename = 'hk.txt' 
		sci_filename = 'sci.txt'
		desc = ( "%s - first byte should always be 0x01\n"
		"%s - first byte should always be 0x00\n"
		"%s & %s - the next four bytes represent the counter and should increment at a rate determined by SCIENCE CADENCE defined in icu_simulator.ino\n"
		"%s - FIB SCI consists of 10 packets, and the third, sixth and ninth byte should increment by 1, other bytes should be constant,the last byte should be 0x00\n"
		"%s - the next three bytes represent the number of fib, fob and fsc which are contained in the pc packet\n"
		"%s - FOB_SCI consists of 10 packets, and all bytes should be set to zero\n"
		"%s - FSC_SCI consists of 11 packets, every first three bytes increment by one, seventh byte increments by one and the tenth and eleventh byte increment by one - XXX 00 02 02 X 02 02 X X\n"
		"%s - the next 32 bytes in hk.log represent pcu data\n"
		"%s - the next 40 bytes in hk.log represent fib_hk\n"
		"%s - the next 4 bytes in hk.log represent fob_hk\n"
		"%s - the next 52 bytes in hk.log represent fsc_hk\n") % (sci_filename, hk_filename, sci_filename, hk_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename)

		parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=desc)
		parser.add_argument(dest = 'port', help = "serial port of the ICU Simulator unit", type = str)
		parser.add_argument('--logdir', dest = 'logdir', help = "path to store data files", type = str)
		parser.add_argument('--verbose', help = "toggle logging level between debug and info respectively")
		args  = parser.parse_args()
		if args.verbose: 
			logging.basicConfig(filename='icu_sim_debug.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode = 'w', level=logging.DEBUG)
		else: 
			logging.basicConfig(filename='icu_sim_debug.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode = 'w', level=logging.INFO)
		arduino = arduino_due(args.port)
		pkt_handler = packet_handler(arduino.get_port(), args.logdir, sci_filename, hk_filename)
		pkt_handler.start() 
		
		cmd_menu = ("0) Go to Standby Mode \n"
					"1) Set Time Command \n"
				    "2) Set Config Command \n"
				    "3) Science Mode \n"
				    "4) Config Mode \n"
				    "5) Power on fee \n"
				    "6) Power off fee \n"
				    "7) End the script \n")
						
		while True:  
			print(cmd_menu)
			nb = input('please choose an option: ')
			try: 
				choice = int(nb)
			except ValueError as error_msg: 
				print('unable to parse choice as an integer %s' % error_msg)
				logging.debug(error_msg)
				continue 
			choice = choice.to_bytes(1, byteorder = 'big')
			if choice == b'\x02': 
				choice +=  build_config_command_val()
			elif choice == b'\x05' or choice == b'\x06': 
				choice += build_fee_packet() 
			elif choice == b'\x07': 
				pkt_handler.close_connection() 
				break
			arduino.write(choice)
			print(choice)	
		pkt_handler.join()
		print("program end")
