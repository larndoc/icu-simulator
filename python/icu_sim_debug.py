import serial 
import argparse
import logging
import time
import binascii
import os
from threading import Thread

def tokenize(string, length):
    return '    '.join(string[i:i+length] for i in range(2,len(string)-1,length))

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
		self.port = port
	def update(self):
		counter = self.port.read(size = 4)
		data_stream = b'\x00' + counter + self.port.read(size = 129)
		return str(binascii.hexlify(data_stream))
		 
class packet_reciever(Thread):
	#recieves a packet and reads the first byte 
	logdir = ''
	files   = dict()
	start_running = True
	
	def __init__(self, serial_port, logdir): 
		super(packet_reciever, self).__init__()
		self.port = serial_port 
		if logdir is None: 
			self.files = {'fee_sci_tm': 'data/fee_science.log', 'house_keeping' : 'data/hk.log'}
		else: 
			if os.path.exists(self.logdir): 
				self.files = {'fee_sci_tm': (self.logdir + '/fee_science.log', 'a'), 'house_keeping' :(self.logdir + '/hk.log', 'a')}
			else: 
				raise SystemExit 
		self.logdir = logdir 		
		self.serial = self.set_up_serial()

	def set_up_serial(self):
		return serial.Serial(self.port,  115200 , timeout =  0.5)
		
	def run(self):
		self.serial.flushInput()
		s = fee_science(self.serial) 
		h = hk_data(self.serial)
		with open(self.files['house_keeping'], 'a') as infile, open(self.files['fee_sci_tm'], 'a') as infile2:
			while self.start_running: 
					decision_hk_sci = bytes(self.serial.read(size = 1))
					if len(decision_hk_sci) > 0:
						if decision_hk_sci[0] == 0:  
							infile.write("{}\n".format(tokenize(h.update(), 2)))
						elif decision_hk_sci[0] == 1: 
							infile2.write("{}\n".format(tokenize(s.update(), 2)))
							
class fee_science():
		def __init__(self, port): 
			self.port = port
			self.total_count = 0 
		def update(self):	
			counter = self.port.read(size = 4)
			n_fee = self.port.read(size = 3)
			self.total_count += n_fee[0] + n_fee[1] + n_fee[2] 
			logger.info('n_total %s n_fib %s, n_fob %s, n_fsc %s', self.total_count, n_fee[0], n_fee[1], n_fee[2])
			data_stream = b'\x01' + counter + n_fee
			for i in range(0, n_fee[0]): 
				data_stream += self.port.read(size = 10) 			
			for i in range(0, n_fee[1]): 
				data_stream += self.port.read(size = 10)
			for i in range(0, n_fee[2]):
				data_stream += self.port.read(size = 11)
			return str(binascii.hexlify(data_stream)) 
			
if __name__ == '__main__':
		logging.basicConfig(filename='fee_pkt_freq.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
		logger = logging.getLogger('fee_pkt_freq.log')
		logger.setLevel(logging.INFO) 
		logger.info('the first byte in fee_science.log should always be 0x01')
		logger.info('the next four bytes in fee_science.log represent the counter and should increment at a rate determined by SCIENCE CADENCE defined in icu_simulator.ino')
		logger.info('the next three bytes represent the number of fib, fob and fsc which are contained in the pc packet')
		logger.info('FIB SCI consists of 10 packets, and the third, sixth and ninth byte should increment by 1, other bytes should be constant,the last byte should be 0x00')
		logger.info('FOB_SCI consists of 10 packets, and all bytes should be set to zero')
		logger.info('FSC_SCI consists of 11 packets, every first three bytes increment by one, seventh byte increments by one and the tenth and eleventh byte increment by one - XXX 00 02 02 X 02 02 X X')
	
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "serial port of the ICU Simulator unit", type = str)
		parser.add_argument('--logdir', dest = 'logdir', help = "path to store data files", type = str)
		args 	 = parser.parse_args()
	
		pkt_reciever = packet_reciever(parser.parse_args().port, parser.parse_args().logdir)
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
