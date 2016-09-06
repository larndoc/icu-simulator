#a interface that allows the user 
#to communicate with the icu-simulator 
#a log file that keeps track of the total 
#number of fib, fob and fsc in sci mode and any
#debug messages 
#hk file that stores the house keeping data 
#in hexadecimal form and a sci file 
#that stores science data in hexadecimal form 
#in order to log the status of each packet the user MUST enable verbosity.
import serial
import argparse
import logging
import time
import binascii
import os
import glob
import sys
from serial.tools import list_ports
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
	fee_number = ("0> FIB \n" "1> FOB \n" "2> FSC \n")
	print(fee_number)
	fee_interface = input('please choose an input: ')	
	cmd_val = int(fee_interface, 0).to_bytes(1, byteorder = 'big') 
	print (cmd_val)
	if cmd_val == b'\x00' or cmd_val == b'\x01' or cmd_val == b'\x02':
		pass
	else: 
		print('UART interface not in range')
		raise Exception 
	read_write = ("0) read \n" 	"1) write \n")
	print(read_write)
	rm_wr = input('> please choose an input: ')
	rm_wr_val = int(rm_wr, 0).to_bytes(1, byteorder = 'big')
	if rm_wr_val == b'\x00' or rm_wr_val == b'\x01':  
		pass 
	else: 
		print('read write value no in range')
		raise Exception 
	config_id = input('>please enter config id: ')		
	config_id_val = int(config_id, 0).to_bytes(1, byteorder = 'big')
	config_val = input('>please enter config val: ')
	choice = int(config_val, 0).to_bytes(3, byteorder='big')
	return cmd_val + rm_wr_val + config_id_val + choice

	
def build_fee_packet(): 	
	"""the function is only triggered 
	only if the user enters '5' or '6' 
	and wishes to activate/deactivate 
	an fee. the user is given a set of
	options to choose from which indicate 
	which fee does he want to enable/disable, 
	try catch block to deal with malformed input"""
	fee_number = ("0> FIB \n" "1> FOB \n" "2> FSC \n")
	print(fee_number)
	fee_interface = input('please choose an input: ')
	fee_interface_val = int(fee_interface, 0).to_bytes(1, byteorder = 'big')
	if fee_interface_val == b'\x00' or fee_interface_val == b'\x01' or fee_interface_val == b'\x02':
		pass 
	else:
		print('UART interface not in range')
		raise Exception
	return fee_interface_val 

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
		"""extract data_stream in bytes and return its hexadecimal representation"""
		size_t = int.from_bytes(size,byteorder = 'big', signed = False) #this is the true size of the packet excluding the first two bytes that represent the size of the packet 
		counter = self.__port.read(size = 4)
		data = self.__port.read(size = 129)
		data_stream = b'\x00' + counter + data
		if size_t != len(data_stream):
			logging.warning('house_keeping_packet malformed!')
			logging.debug('expected HK: ' + str(size_t) + ' recieved: ' + str(len(data_stream))) 
			if len(counter) is not 4:
				logging.warning('could not read counter')
			elif len(data) is not 129: 
				logging.warning('could not read data')
		else: 
			logging.info('recieved house_keeping packet')
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
		try: 
			self.__port = serial.Serial(port, 115200, timeout = None)
		except: 
			error_msg = ''
			logging.error('unable to connect to port')
			print('unable to connect to port ' + port + ',list of available ports:')
			serial_ports = list_ports.comports()
			for p in serial_ports: 
				if "COM" or "ttyACM" in p: 
					print(p)		
			raise SystemExit()
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
		"""indicates that we want the thread to terminate, go back to standby mode"""
		self.__port.write(b'\x00')
		self.__active = False; 
	
	def __init__(self, port, logdir, sci_filename, hk_filename):
		super(packet_handler, self).__init__()
		self.__port = port
		self.__filename["hk"] = hk_filename
		self.__filename["sci"] = sci_filename
		if logdir is None: 
			logdir = '.'
		else: 
			logdir = logdir.rstrip("/")
		if os.path.exists(logdir): 
			for key, value in self.__filename.items(): 
				self.__filename[key] = logdir + "/" + value
		else: 
			#the directory doesn't exist!
			logging.error('the user tried to logon to an invalid directory')
			raise SystemExit()

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
		"""the class primarily
		deals with extracting 
		the science data and depositing 
		it in the sci.txt file - we initialize the object 
		with the serial port and total_count which 
		is used to keep track of the total number of fib 
		fob and fsc packets recieved by the icu - simulator. 
		depending on the number of fib, fob and fsc we 
		pull out relevant data and append b'\x01' 
		at the start of the stream 
		to indicate that it is a science packet - 
		we also check to see if we do recieve the 
		number of packets indicated by the first two 
		bytes in the stream"""	
		def __init__(self, port): 
			self.__port = port
			self.total_count = 0
		def update(self, size):	
			size = int.from_bytes(size ,byteorder = 'big', signed = False)
			counter = self.__port.read(size = 4)
			n_fee = self.__port.read(size = 3)
			
			self.total_count += n_fee[0] + n_fee[1] + n_fee[2] 
			logging.info('recieved SCI packet: n_total %s n_fib %s, n_fob %s, n_fsc %s', self.total_count, n_fee[0], n_fee[1], n_fee[2])
			
			data_stream = b'\x01' + counter + n_fee
			
			for i in range(0, n_fee[0]): 
				data_stream += self.__port.read(size = 10) 			
			for i in range(0, n_fee[1]): 
				data_stream += self.__port.read(size = 10)
			for i in range(0, n_fee[2]):
				data_stream += self.__port.read(size = 11)
			if size != len(data_stream): 
				logging.warning('sci packet malformed!')
				logging.debug('expected SCI: ' + str(size_t) + ' recieved: ' + str(len(data_stream)))
				if len(counter) is not 4: 
					logging.warning('could not read counter')
				if len(n_fee) is not 3: 
					logging.warning('could not read n_fee')
				else: 
					logging.warning('could not read data')
			return str(binascii.hexlify(data_stream)) 
			
if __name__ == '__main__':
		hk_filename = 'hk.txt' 
		sci_filename = 'sci.txt'
		desc = ( "%s - first byte should always be 0x01\n"
		"%s - first byte should always be 0x00\n"
		"%s & %s - the next four bytes represent the counter and should increment at a rate determined by SCIENCE CADENCE defined in icu_simulator.ino\n"
		"%s - the next three bytes x, y and z determine the number of fib, fob and fsc packets in the PC packet, the size of the data is given by s = 10(x + y) + 11z \n"
		"%s - the next 32 bytes in hk.log represent pcu data\n"
		"%s - the next 40 bytes in hk.log represent fib_hk\n"
		"%s - the next 4 bytes in hk.log represent fob_hk\n"
		"%s - the next 52 bytes in hk.log represent fsc_hk\n") % (sci_filename, hk_filename, sci_filename, hk_filename, sci_filename, hk_filename, hk_filename, hk_filename, hk_filename)
		parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=desc)
		parser.add_argument(dest = 'port', help = "serial port of the ICU Simulator unit", type = str)
		parser.add_argument('--logdir', dest = 'logdir', help = "path to store data files", type = str)
		parser.add_argument('-v', '--verbose', action='count', help = "varying output verbosity")
		args  = parser.parse_args()
		if args.verbose == None:
			loglevel = logging.WARNING
		elif args.verbose == 1:
			loglevel = logging.INFO
		else:
			loglevel = logging.DEBUG		
		logging.basicConfig(filename = 'icu_sim_debug.log', format = '%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode = 'w', level=loglevel)
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
		error_msg = ''				
		while True:  
			print(cmd_menu)
			nb = input('please choose an option: ')
			error_msg = ''
			try: 
				try:
					choice = int(nb, 0).to_bytes(1, byteorder = 'big')
					print (choice)
				except:
					error_msg = "incorrect data type"
					print(error_msg)
					raise ValueError
				if (choice >= b'\x00')and (choice < b'\x08'):
					pass
				else: 
					error_msg = "out of bound instruction, your instruction will be thrown away"
					print(error_msg)
					raise ValueError 
				if choice == b'\x02': 
					try: 
						choice +=  build_config_command_val()
					except:  
						error_msg = "you will not be able to write command out to the icu-simulator"
						print(error_msg)
						raise ValueError
				elif choice == b'\x05' or choice == b'\x06':  
					try:
						choice += build_fee_packet()
					except: 
						error_msg = 'you will not be able to write command out to the icu-simulator'
						print(error_msg)
						raise ValueError
				elif choice == b'\x07':
					pkt_handler.close_connection() 
					break
				arduino.write(choice)
				print("you have just sent the following command to the icu-simulator: " + str(choice))
			except ValueError: 
				logging.warning(error_msg)
			#the ICU - Simulator takes care of any invalid commands - we CAN write invalid commands such 9, 0x0A etc but the ICU - Simulator is just going to discard them
				
		pkt_handler.join()
		print("program end")
