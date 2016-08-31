import serial 
import argparse
import logging
import time
import binascii
import os
from threading import Thread

def tokenize(string, length):
    return ' '.join(string[i:i+length] for i in range(2,len(string)-1,length)) + "\n"

def build_config_command_val(fee_number): 
	print(fee_number)
	cmd = input('> please choose an input: ')	
	cmd_val = (int(cmd, 0)).to_bytes(1, byteorder = 'big')
	read_write = (
	"0) read \n" 
	"1) write \n"
	)
	print(read_write)
	rm_wr = input('> please choose an input: ')
	rm_wr_val = int(rm_wr, 0).to_bytes(1, byteorder = 'big')
	config_id = input('>please enter config id: ')		
	config_id_val = int(config_id, 0).to_bytes(1, byteorder = 'big')
	config_val = input('>please enter config val: ')
	choice = int(config_val, 0).to_bytes(3, byteorder='big')
	return cmd_val + rm_wr_val + config_id_val + choice
	
def build_fee_packet(fee_number): 						
	print(fee_number)
	fee_interface = input('please choose an input: ')
	return int(fee_interface, 0).to_bytes(1, byteorder = 'big')

class hk_data: 	
	def __init__(self, port): 
		self.__port = port
	def update(self):
		size = int.from_bytes(self.__port.read(size = 2),byteorder = 'big', signed = False) #this is the true size of the packet excluding the first two bytes that represent the size of the packet 
		counter = self.__port.read(size = 4)
		data = self.__port.read(size = 129)
		data_stream = b'\x00' + counter + data
		if len(counter) + len(data_stream) is not size: 
			logger.info('house_keeping_packet malformed!')
			if len(counter) is not 4:
				logger.info('could not read counter')
			elif len(data) is not 129: 
				logger.info('could not read data')
		else: 
			logger.info('recieved house_keeping packet, status OK')
		#we still want to se the contents of the malformed packet
		return str(binascii.hexlify(data_stream))
		 
class packet_reciever(Thread):
	#recieves a packet and reads the first byte 
	logdir = ''
	__filename   = dict()
	__files 		 = dict()
	start_running = True
	def __init__(self, serial_port, logdir, sci_filename, hk_filename): 
		super(packet_reciever, self).__init__()
		self.__serial = self.set_up_serial(serial_port)
		self.__filename["hk"] = sci_filename
		self.__filename["sci"] = hk_filename
		if logdir is None: 
			logdir = "data"
		else: 
			logdir = logdir.rstrip("/")
		if os.path.exists(logdir): 
			for key, value in self.__filename.items(): 
				self.__files[key] = logdir + "/" + value
		else: 
			raise SystemExit('not a valid directory')	

	def set_up_serial(self, serial_port):
		return serial.Serial(serial_port,  115200 , timeout =  None)
		
	def run(self):
		self.__serial.flushInput()
		s = fee_science(self.__serial) 
		h = hk_data(self.__serial)
		with open(self.__files['hk'], 'w') as f_hk, open(self.__files['sci'], 'w') as f_sci:
			f_sci.write('status time_3 time_2 time_1 time_0 n_fib n_fob n_fsc + \n')
			header = [] 
			header.append("status time_3 time_2 time_1 time_0") 
			header.append(" ".join(["pcu"+str(v) for v in range(31,-1,-1)]))
			header.append(" ".join(["fib"+str(v) for v in range(39,-1,-1)]))
			header.append(" ".join(["fob"+str(v) for v in range(3,-1,-1)]))
			header.append(" ".join(["fsc"+str(v) for v in range(51,-1,-1)]))
			f_hk.write(" ".join(header) + "\n") 
			while self.start_running: 
					decision_hk_sci = self.__serial.read(size = 1)
					if len(decision_hk_sci) > 0:
						if decision_hk_sci[0] == 0:  
							f_hk.write(tokenize(h.update(), 2))
						elif decision_hk_sci[0] == 1: 
							f_sci.write(tokenize(s.update(), 2))
							
class fee_science():
		def __init__(self, port): 
			self.__port = port
			self.total_count = 0
		def update(self):	
			size = int.from_bytes(self.__port.read(size = 2),byteorder = 'big', signed = False)
			counter = self.__port.read(size = 4)
			n_fee = self.__port.read(size = 3)
			
			self.total_count += n_fee[0] + n_fee[1] + n_fee[2] 
			logger.info('n_total %s n_fib %s, n_fob %s, n_fsc %s', self.total_count, n_fee[0], n_fee[1], n_fee[2])
			
			data_stream = b'\x01' + counter + n_fee
			
			for i in range(0, n_fee[0]): 
				data_stream += self.port.read(size = 10) 			
			for i in range(0, n_fee[1]): 
				data_stream += self.port.read(size = 10)
			for i in range(0, n_fee[2]):
				data_stream += self.port.read(size = 11)
			if size is not len(data_stream): 
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
		% (sci_filename, sci_filename, sci_filename, hk_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename, sci_filename)
		)
		args  = parser.parse_args()
		pkt_reciever = packet_reciever(args.port, args.logdir, sci_filename, hk_filename)
		pkt_reciever.start() 
		while not pkt_reciever.is_alive(): 
			pass 
		time.sleep(2)
		## needed as arduino needs to come up, do not remove. 
		## should update the global time here as it is more readable 
		cmd_menu = ("1) Set Time Command \n"
				   "2) Set Config Command \n"
				   "3) Science Mode \n"
				   "4) Config Mode \n"
				   "5) Power on fee \n"
				   "6) Power off fee \n"
				   "7) End the script \n")
						
		fee_number 	= ("0> FIB \n"
				   "1> FOB \n"
				   "2> FSC \n")
		command = ''
		while pkt_reciever.start_running:  
			print(cmd_menu)
			nb = input('please choose an option: ')
			try: 
				choice = int(nb)
			except ValueError as error_msg: 
				print('unable to parse choice as an integer %s' % error_msg)
				logging.debug(error_msg)
				continue 
			if choice == 2: 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big') + build_config_command_val(fee_number));
			elif choice == 4:
				command = ((int(nb, 16).to_bytes(1, byteorder = 'big'))); 
			elif choice == 3:
				pkt_reciever.begin_receiving = True
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big'))
			elif choice == 5 or choice == 6: 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big')) + build_fee_packet(fee_number) 
			elif choice == 7: 
				pkt_reciever.start_running = False
				switch_off = True
			if choice != 7 and pkt_reciever.is_alive() == True:
				pkt_reciever.serial.write(bytes(command));
			print(command)	
		pkt_reciever.join()
		print("program end")
