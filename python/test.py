import serial 
import argparse
import datetime
import logging
import time
import binascii
from threading import Thread

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
<<<<<<< HEAD
			self.house_keeping_data = [] 
		def update(self, values): 
			self.house_keeping_data = []
			self.house_keeping_data.append(pcu_data(self.port.read(size = 32))) 
			self.house_keeping_data.append(fib_hk_data(self.port.read(size = 40)))
			self.house_keeping_data.append(fob_hk_data(self.port.read(size = 4)))
			self.house_keeping_data.append(fsc_hk_data(self.port.read(size = 51)))
			for i in range(0, 4):
				self.house_keeping_data[i].update(values = values)
=======
		def update(self, values):
			#values['house_keeping'] = '' 
			hk_packets = [self.port.read(size = 32), self.port.read(size = 40), self.port.read(size = 4), self.port.read(size = 53)]
			i = 0
			for i in range(0, 4): 
				values['house_keeping'] += hk_packets[i]
				i += 1
>>>>>>> ce4117f5f9f40d2f24f7e065ccd023bde817e13e
		 
class packet_reciever(Thread):
	#recieves a packet and reads the first byte 
	
	hk_values = dict()
	sci_values = dict() 
	files   = dict()
	start_running = True
	
	def __init__(self, serial_port, logdir): 
		super(packet_reciever, self).__init__()
		self.port = serial_port 
		self.logdir = logdir 		
		self.serial = self.set_up_serial()
		
	
	def set_up_serial(self):
		return serial.Serial(self.port,  115200 , timeout =  0.5)
		
	def update_global_time(self): 
		return datetime.datetime.now()
	def update_files(self): 
		self.files = {'fee_sci_tm': 'data/fee_science.log', 'house_keeping' : 'data/hk.log'}

	def run(self): 
		self.update_files()
		s = fee_science(self.serial) 
		h = hk_data(self.serial)
		values = [self.hk_values, self.sci_values]
		while self.start_running:
			while self.serial.inWaiting(): 
				decision_hk_sci = bytes(self.serial.read(size = 1))
<<<<<<< HEAD
				if(decision_hk_sci == b'\x01'):  
					for key in self.sci_values: 
						self.sci_values[key] = ''
					with open(self.files['fib_sci_tm'], 'a') as infile, open(self.files['fob_sci_tm'], 'a') as infile2, open(self.files['fsc_sci_tm'], 'a') as infile3: 
						a = (self.serial.read(size = 4))
						counter = int.from_bytes(a, byteorder = 'big', signed = True)
						self.time = (self.current_time + datetime.timedelta(seconds = counter/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
						s = fee_science(self.serial)
						s.update(self.sci_values)
						for key in self.sci_values:  
							if self.sci_values[key] != '':
								if key == 'fib_sci_tm': 
									infile.write("{}\n".format("{},".format(self.time)   + self.sci_values[key][:-1]))
								elif key == 'fob_sci_tm':  
									infile2.write("{}\n".format("{},".format(self.time) + self.sci_values[key][:-1]))
								elif key == 'fsc_sci_tm':  
									infile3.write("{}\n".format("{},".format(self.time) + self.sci_values[key][:-1]))
				if(decision_hk_sci == b'\x00'):
					for key in self.hk_values: 
						self.hk_values[key] = ''
					with open (self.files['fib_hk_tm'], 'a') as infile, open(self.files['fob_hk_tm'], 'a') as infile2, open(self.files['fsc_hk_tm'], 'a') as infile3, open(self.files['pcu_data'], 'a') as infile4:
						counter = int.from_bytes(self.serial.read(size = 4), byteorder = 'big')
						self.time = (self.current_time + datetime.timedelta(seconds = counter/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
						h = hk_data(self.serial)
						h.update(self.hk_values)
						for key in self.hk_values: 
							if key == 'fib_hk_tm': 
								infile.write("{}\n".format("{},".format(self.time) + self.hk_values[key][:-1]))
							elif key == 'fob_hk_tm':  
								infile2.write("{}\n".format("{},".format(self.time) + self.hk_values[key][:-1]))
							elif key == 'fsc_hk_tm':  
								infile3.write("{}\n".format("{},".format(self.time) + self.hk_values[key][:-1]))
							elif key == 'pcu_data':  
								infile4.write("{}\n".format("{},".format(self.time) + self.hk_values[key][:-1]))
							
=======
				counter = bytes(self.serial.read(size = 4))
				if decision_hk_sci[0] == 0: 
					values[0]['house_keeping'] = decision_hk_sci 
					h.update(values[0])
				if decision_hk_sci[0] == 1:
					values[1]['fee_sci_tm'] = decision_hk_sci
					s.update(values[1])
				for key,f in values[decision_hk_sci[0]].items(): 
						with open(self.files[key], 'a') as infile: 
							if f != '': 
								infile.write("{}\n".format(binascii.hexlify(counter +  f[:-1])))


>>>>>>> ce4117f5f9f40d2f24f7e065ccd023bde817e13e
class fee_science():
		def __init__(self, port): 
			self.port = port
		def update(self, values):
			n_fee = self.port.read(size = 3)
			values['fee_sci_tm'] += n_fee
			for i in range(0, n_fee[0]): 
				values['fee_sci_tm'] += self.port.read(size = 10) 
			
			for i in range(0, n_fee[1]): 
				values['fee_sci_tm'] += self.port.read(size = 10) 
			
			for i in range(0, n_fee[2]):
				values['fee_sci_tm'] += self.port.read(size = 11)
											
if __name__ == '__main__':
		logging.basicConfig(filename='debugger.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
		logger = logging.getLogger()
		switch_off = False
		logger.setLevel(logging.INFO) 
	
	
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
		
		
		cmd_menu	= ("1) Set Time Command \n"
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
		while(switch_off == False):  
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
