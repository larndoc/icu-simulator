import serial i
import argparse
import datetime
import collections
import logging
import time
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
		def update(self, current_time, counter, values):
			time = (current_time + datetime.timedelta(seconds = counter/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
			hk_packets = [pcu_data(self.port.read(size = 32)), fib_hk_data(self.port.read(size = 40)), fob_hk_data(self.port.read(size = 4)), fsc_hk_data(self.port.read(size = 53))]
			i = 0
			for key in values: 
				values[key] = time + hk_packets[i].update() + '\n'
				i += 1
				
		 
class packet_reciever(Thread):
	#recieves a packet and reads the first byte 
	values = (('pcu_data', []), ('fib_hk_tm', []))
	hk_values = (('pcu_data',''), ('fib_hk_tm',''), ('fob_hk_tm', ''), ('fsc_hk_tm', ''))
	sci_values = (('fib_sci_tm', ''), ('fob_sci_tm', ''), ('fsc_sci_tm', ''))
	hk_values = collections.OrderedDict(hk_values)
	sci_values = collections.OrderedDict(sci_values) 
	files   = dict()
	time = ''
	start_running = True
	labels = dict()
	
	def __init__(self, serial_port, logdir): 
		self.labels = {'fib_sci_tm' : ['Time', 'Bx', 'By', 'Bz', 'status'], 
			       'fob_sci_tm'  : ['Time', 'Bx', 'By', 'Bz'],
			       'fsc_sci_tm' : ['Time',	'Sensor_Laser',	'Laser_Micro', 'Zeeman','Sci_Data_ID','Sci_Data','Timestamp'],
			       'fib_hk_tm' : ['Time','Status_HB','Status_LB','LUP_cnt','P1V5','P3V3','P5V','N5V','P8V','P12V','P1I5','P3I3','P5I','N5I','P8I','P12I','TE','TS1','TS2','Checksum','CMD_exec_cnt','ICU_err_cnt','Last_cmd','Last_err','HK_req_cnt','sync_count']
					   ,'fob_hk_tm' : ['Time','Delay/Advance Val', 'ICU packet checksum', 'ICU command count', 'sync_pulse_count']
					   ,'fsc_hk_tm' : ['Time', 'Peregrine_Lock','Sensor_Temp_A','Sensor_Temp_B','Sensor_Temp_Duty_Cycle','Laser_Temp_A','Laser_Temp_B','Laser_Temp_Duty_Cycle','Laser_Current','Laser_Current_Zero_Cross','Microwave_Ref','Microwave_Ref_Zero_Cross','Zeeman_Freq_Zero_Cross','PCB_Temp_A','PCB_Temp_B','Laser_Diode_Voltage','Diode_Optical_Power','P2V4','P3V3','P8V','N8V','P12V','PCB_Temp_C','PCB_Temp_D','PCB_Temp_E','ICU_Checksum','ICU_Command_Count','ICU_Sync_Count']
					   ,'pcu_data'  : ['Time','I_FIB','I_FOB','I_FSC','I_P3V3','I_FIBH','I_FOBH','I_FSCH','I_P1V8','Temp','V_P2V4','V_P3V3','V_P12V','V_P8V','V_N8V','V_P5V','V_N5V']}
		super(packet_reciever, self).__init__()
		self.port = serial_port 
		self.logdir = logdir 		
		self.serial = self.set_up_serial()
		
	
	def set_up_serial(self):
		return serial.Serial(self.port,  115200 , timeout =  0.5)
		
	def update_global_time(self): 
		return datetime.datetime.now()
	def update_files(self, t_str): 
		self.files = {'fib_sci_tm': 'data/FIB_SCI_TM_' + t_str + '.csv', 'fob_sci_tm' : 'data/FOB_SCI_TM_' + t_str + '.csv', 'fsc_sci_tm' : 'data/FSC_SCI_TM_' + t_str + '.csv'
					,'fib_hk_tm': 'data/FIB_HK_TM_' + t_str + '.csv', 'fob_hk_tm' : 'data/FOB_HK_TM_' + t_str + '.csv', 'fsc_hk_tm' : 'data/FSC_HK_TM_' + t_str + '.csv', 'pcu_data' : 'data/PCU' + t_str + '.csv'}

	def run(self): 
		self.current_time = self.update_global_time()
		self.update_files(self.current_time.strftime("%Y%m%d_%H%M%S"))
		s = fee_science(self.serial) 
		h = hk_data(self.serial)
		values = [self.hk_values, self.sci_values]
		for key in self.files:
			with open (self.files[key], 'a') as infile:  
				infile.write("{}\n".format(','.join(self.labels[key])))
		while self.start_running:
			while self.serial.inWaiting(): 
				decision_hk_sci = bytes(self.serial.read(size = 1))
				counter = int.from_bytes(self.serial.read(size = 4), byteorder = 'big')
				if decision_hk_sci[0] == 0: 
					h.update(self.current_time, counter, values[0])
				elif decision_hk_sci[0] == 1: 
					s.update(self.current_time, counter, values[1])
					for key,f in values[decision_hk_sci[0]].items(): 
						with open(self.files[key], 'a') as infile: 
							if f != '': 
								infile.write("{}\n".format( f[:-1]))


class fee_science():
		def __init__(self, port): 
			self.port = port
		def update(self, current_time, counter, values):
			fee_packet = self.port.read(size = 3)
			values["fib_sci_tm"] = ''
			values["fob_sci_tm"] = '' 
			values["fsc_sci_tm"] = ''
			count_val = counter
			for i in range(0, int(fee_packet[0])): 
				f = fib_sci(self.port.read(size = 10))
				time = (current_time + datetime.timedelta(seconds = counter/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
				values["fib_sci_tm"] += "{},".format(time) + f.update() + '\n'
				count_val += 1
			
			count_val = counter	
			for i in range(0, int(fee_packet[1])): 
				f = fob_sci(self.port.read(size = 10))
				time = (current_time + datetime.timedelta(seconds = count_val/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
				values["fob_sci_tm"] += "{},".format(time) + f.update() + '\n' 
				count_val += 1 
			
			count_val = counter 
			for i in range(0, int(fee_packet[2])): 
				f = fsc_sci(self.port.read(size = 11))
				time = (current_time + datetime.timedelta(seconds = count_val/128)).strftime("%Y-%m-%dT%H:%M:%S.%f")
				values["fsc_sci_tm"] += "{},".format(time) + f.update() + '\n'
				count_val += 1

def get_coord(data, byteorder): 
	return "{},".format(int.from_bytes(data, byteorder, signed = True))

def get_status(data): 
	return "{},".format(data)
					
class fib_sci():  
	def __init__(self, data): 
		self.data = data
	def update(self): 
		data_stream =  get_coord(self.data[0:3], byteorder = 'big')  # x
		data_stream += get_coord(self.data[3:6], byteorder = 'big')  # y
		data_stream += get_coord(self.data[6:9], byteorder = 'big')  # z
		data_stream += get_status(self.data[9]) # status
		return data_stream
	
class fob_sci(): 
	def __init__(self, data): 
		self.data = data 
	def update(self): 
		data_stream =  get_coord(self.data[0:3], byteorder = 'little')
		data_stream += get_coord(self.data[3:6], byteorder = 'little')
		data_stream += get_coord(self.data[6:9], byteorder = 'little')
		return data_stream 

def get_sensor_laser(data): 
	return "{},".format(data) 

def get_laser_micro(data): 
	return "{},".format(data) 

def get_zeeman(data): 
	return "{},".format(data)

def get_sci_data_id(data): 
	return "{},".format(data) 

def get_sci_data(data):
	return "{},".format(int.from_bytes(data,byteorder = 'big', signed = False))

def get_time_stamp(data):
	return "{}".format(int.from_bytes(data, byteorder = 'big', signed = False)) 
class fsc_sci():
	def __init__(self, data): 
		self.data = data 
	def update(self):
		data_stream  = get_sensor_laser(self.data[0]) 
		data_stream += get_laser_micro(self.data[1]) 
		data_stream += get_zeeman(self.data[2]) 
		data_stream += get_sci_data_id(self.data[3]) 
		data_stream += get_sci_data(self.data[4:8]) 
		data_stream += get_time_stamp(self.data[8:11])
		return data_stream

class pcu_data():
	def __init__(self, data): 
		self.data = data 
	def update(self):
		data_stream = ''
		for i in filter(lambda w : w % 2 == 0, range(0, 32)): 
			data_stream += "{},".format(int.from_bytes(self.data[i:i+2], byteorder = 'big'))
		return data_stream 

class fib_hk_data():		
	def __init__(self, data): 
		self.data = data
	def update(self):
		data_stream = '' 
		for i in range(0, 3):
			data_stream += "{},".format(int(self.data[i]))
		for i in filter(lambda w : w % 2 == 0, range(1, 32)):
			data_stream += ("{},".format(int.from_bytes(self.data[(i + 2): (i + 4)], byteorder = 'big')))
		for i in range(33, len(self.data)): 
			data_stream += "{},".format(int(self.data[i]))
		return data_stream 

class fob_hk_data():
	def __init__(self, data): 
		self.data = data
	def update(self): 
		data_stream = '' 
		for i in range(0, len(self.data)): 
			data_stream += ("{},".format(int.from_bytes(self.data[(i): (i + 2)], byteorder = 'big')))
		return data_stream 
			
class fsc_hk_data():
	def __init__(self, data): 
		self.data = data 
	def update(self): 
		#extracting bytes 0 
		data_stream = "{},".format(int(self.data[0]))
			
		#extracting bytes 1 - 2 and 3 - 4
		for i in filter(lambda w : w % 2 == 0, range(1, 5)):
			data_stream += "{},".format(int.from_bytes(self.data[i: (i + 2)], byteorder = 'big'))
			
		#extracting bytes 5-7
			data_stream += "{},".format(int.from_bytes(self.data[5 : 7], byteorder = 'big'))
			
			#extracting bytes 7 - 8 and 9 - 10
			for i in filter(lambda w : w % 2 == 0, range(7, 11)): 
				data_stream += "{},".format(int.from_bytes(self.data[ i : (i + 2)], byteorder = 'big'))
			
			data_stream += "{},".format(int.from_bytes(self.data[11: 13], byteorder = 'big'))
			
			#extract bytes 13 - 15 and 16 - 18
			for i in filter(lambda w : w % 3 == 1, range(13, 19)):
				data_stream += "{},".format(int.from_bytes(self.data[i: (i + 3)], byteorder = 'big'))
			
			for i in filter(lambda w : w % 2 == 0, range(19, 23)):
				data_stream += "{},".format(int.from_bytes(self.data[i:(i + 2)], byteorder = 'big'))
		
			data_stream += "{},".format(int.from_bytes(self.data[23:26], byteorder = 'big'))
			
			for i in filter(lambda w : w % 2 == 0, range(26, 30)):
				data_stream += "{},".format(int.from_bytes(self.data[i : (i + 2)], byteorder = 'big'))
				
			data_stream += "{},".format(int.from_bytes(self.data[30 : 32], byteorder = 'big'))
			data_stream  += "{},".format(int.from_bytes(self.data[32: 34], byteorder = 'big'))
			
			for i in filter(lambda w : w % 2 == 0, range(34, 50)):
				data_stream += "{},".format(int.from_bytes(self.data[i : (i + 2)], byteorder = 'big'))
					
			for i in range(50, 53): 
				data_stream  += 'a'
			return data_stream
		
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
