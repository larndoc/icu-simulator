import serial 
import argparse
import logging
import time
import binascii
import os
from threading import Thread

def tokenize(string, length):
    return ' '.join(string[i:i+length] for i in range(2,len(string)-1,length)) + "\n"

def build_config_command_val(): 
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
	try:
		fee_number 	= ("0> FIB \n" "1> FOB \n" "2> FSC \n")
		print(fee_number)
		fee_interface = input('please choose an input: ')
		fee_interface_val = int(fee_interface, 0).to_bytes(1, byteorder = 'big')
		return fee_interface_val 
	except: 
		print('could not build fee packet - you will not able to write the following command to the arduino %s' % error_msg)
		logging.debug(error_msg)

class hk_data: 	
	def __init__(self, port): 
		self.__port = port
	def update(self, size):
		size_t = int.from_bytes(size,byteorder = 'big', signed = False) #this is the true size of the packet excluding the first two bytes that represent the size of the packet 
		counter = self.__port.read(size = 4)
		data = self.__port.read(size = 129)
		data_stream = b'\x00' + counter + data
		if size_t != len(data_stream): 
			print('house_keeping packet malformed')
			logger.info('house_keeping_packet malformed!')
			if len(counter) is not 4:
				logger.info('could not read counter')
			elif len(data) is not 129: 
				logger.info('could not read data')
		else: 
			logger.info('recieved house_keeping packet, status OK')
		#we still want to se the contents of the malformed packet
		return str(binascii.hexlify(data_stream))
		 	 
class arduino_due():
	def __init__(self, port): 
		self.__port = serial.Serial(port, 115200, timeout = None)
		time.sleep(1)
		# any other initialisation
		
	def write(self, data): 
		self.__port.write(bytes(data))
		
	def read(self):
		return self.__port.read()
		

		 
class packet_handler(Thread):
	#recieves a packet and reads the first byte 
	__filename   = dict()
	start_running = True
	
	def __init__(self, serial_port, logdir, sci_filename, hk_filename): 
		super(packet_handler, self).__init__()
		self.__serial = serial_port
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
			raise SystemExit('not a valid directory')	
		
	def run(self):
		self.__serial.flushInput()
		s = fee_science(self.__serial) 
		h = hk_data(self.__serial)
		with open(self.__filename['hk'], 'w') as f_hk, open(self.__filename['sci'], 'w') as f_sci:
			f_sci.write('status time_3 time_2 time_1 time_0 n_fib n_fob n_fsc' + "\n")
			header = [] 
			header.append("status time_3 time_2 time_1 time_0") 
			header.append(" ".join(["pcu"+str(v) for v in range(31,-1,-1)]))
			header.append(" ".join(["fib"+str(v) for v in range(39,-1,-1)]))
			header.append(" ".join(["fob"+str(v) for v in range(3,-1,-1)]))
			header.append(" ".join(["fsc"+str(v) for v in range(51,-1,-1)]))
			f_hk.write("{}\n".format(" ".join(header))) 
			while self.start_running: 
					size = self.__serial.read(size = 2)
					decision_hk_sci = self.__serial.read(size = 1)
					if len(decision_hk_sci) > 0:
						if decision_hk_sci[0] == 0:  
							f_hk.write(tokenize(h.update(size), 2))
							f_hk.flush()
						elif decision_hk_sci[0] == 1: 
							f_sci.write(tokenize(s.update(size), 2))
							f_sci.flush()
							
class fee_science():
		def __init__(self, port): 
			self.__port = port
			self.total_count = 0
		def update(self, size):	
			size = int.from_bytes(size ,byteorder = 'big', signed = False)
			counter = self.__port.read(size = 4)
			n_fee = self.__port.read(size = 3)
			
			self.total_count += n_fee[0] + n_fee[1] + n_fee[2] 
			logger.info('n_total %s n_fib %s, n_fob %s, n_fsc %s', self.total_count, n_fee[0], n_fee[1], n_fee[2])
			
			data_stream = b'\x01' + counter + n_fee
			
			for i in range(0, n_fee[0]): 
				data_stream += self.__port.read(size = 10) 			
			for i in range(0, n_fee[1]): 
				data_stream += self.__port.read(size = 10)
			for i in range(0, n_fee[2]):
				data_stream += self.__port.read(size = 11)
			if size != len(data_stream): 
				print('sci packet malformed!')
				logger.info('sci packet malformed!')
				if len(counter) is not 4: 
					logger.info('could not read counter')
				if len(n_fee) is not 3: 
					logger.info('could not read n_fee')
				else: 
					logger.info('could not read data')
			else: 
					logger.info('recieved house_keeping_packet, status OK')
			return str(binascii.hexlify(data_stream)) 
			
if __name__ == '__main__':
		logging.basicConfig(filename='icu_sim_debug.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filemode = 'w')
		logger = logging.getLogger('icu_sim_debug.log')
		logger.setLevel(logging.INFO) 
		hk_filename = 'hk.txt' 
		sci_filename = 'sci.txt' 
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "serial port of the ICU Simulator unit", type = str)
		parser.add_argument('--logdir', dest = 'logdir', help = "path to store data files", type = str)
		parser.add_argument('--overview', help =  """ %s -first byte should always be 0x01 %s-first byte should always be 0x00
		%s 'and' %s-the next four bytes represent the counter and should increment at a rate determined by SCIENCE CADENCE defined in icu_simulator.ino
		%s -FIB SCI consists of 10 packets, and the third, sixth and ninth byte should increment by 1, other bytes should be constant,the last byte should be 0x00
		%s -the next three bytes represent the number of fib, fob and fsc which are contained in the pc packet
		%s -FOB_SCI consists of 10 packets, and all bytes should be set to zero
		%s -FSC_SCI consists of 11 packets, every first three bytes increment by one, seventh byte increments by one and the tenth and eleventh byte increment by one - XXX 00 02 02 X 02 02 X X
		%s -the next 32 bytes in hk.log represent pcu data 
		%s -the next 40 bytes in hk.log represent fib_hk
		%s -the next 4 bytes in hk.log represent fob_hk %s -the next 52 bytes in hk.log represent fsc_hk"""
		% (sci_filename, sci_filename, sci_filename, hk_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename))
		args  = parser.parse_args()
		arduino = arduino_due(args.port)
		pkt_handler = packet_handler(arduino, args.logdir, sci_filename, hk_filename)		
		pkt_handler.start() 
		while not pkt_handler.is_alive(): 
			pass 
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
				pkt_handler.start_running = False
				break;
			arduino.write(choice)
			print(choice)	
		pkt_handler.join()
		print("program end")
