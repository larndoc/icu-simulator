#plot power spectral density of the sawtooth waveform? 
#plot frequency sprectrum of the sawtooth waveform? 

import serial 
import argparse
import datetime
import collections
import logging
import time
from threading import Thread

def to_bytes(n, size, byteorder): 
	if byteorder == 'big': 
		return 
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
	n = int(config_val, )
	choice = int(config_val, 0).to_bytes(3, byteorder='big')
	return cmd_val + rm_wr_val + config_id_val + choice
	
def build_fee_packet(fee_number): 						
	print(fee_number)
	fee_interface = input('please choose an input: ')
	n = int(fee_interface, 0).to_bytes(1, byteorder = 'big')
	return  n
	

#def debug_information(data): 
#	print(binascii.hexlify(data))
	
	
class hk_data: 	
		#load the data into appropiate labels and then extract it from packet_reciever where it is written into files
		def __init__(self, port, values): 
			self.update(port,  values)
		
		def update(self, port, values): 
			p = pcu_data(port.read(size = 32),  values)
			fi = fib_hk_data(port.read(size = 40), values)  
			fo = fob_hk_data(port.read(size = 4),  values) 
			fs = fsc_hk_data(port.read(size = 51), values)						

	
class file(): 
	files_fib_hk = ''
	def __init__(self, file): 
		self.file = file
		 
class packet_reciever(Thread):
	#recieves a packet and reads the first byte 
	hk_values = collections.OrderedDict()
	sci_values = collections.OrderedDict() 
	baud_rate = 115200 
	timeout = 0.5
	files   = dict()
	time = ''
	files_fib_hk = ''
	sci_labels  = False
	hk_labels   = False
	start_running = True
	labels = dict()
	def __init__(self, serial_port, logdir): 
		self.hk_values['pcu_data'] = ''
		self.hk_values['fib_hk_tm'] = ''
		self.hk_values['fob_hk_tm'] = '' 
		self.hk_values['fsc_hk_tm'] = ''
		
		self.sci_values['fib_sci_tm'] = ''
		self.sci_values['fob_sci_tm'] = ''
		self.sci_values['fsc_sci_tm'] = ''
		super(packet_reciever, self).__init__()
		self.port = serial_port 
		self.logdir = logdir 		
		self.serial = self.set_up_serial()
	
	def set_up_serial(self):
		return serial.Serial(self.port, self.baud_rate, timeout =  self.timeout)
		
	def update_global_time(self): 
		return datetime.datetime.now()
	
	def update_sci_files(self, t_str): 
			self.files["fib_sci_tm"] = 'data\FIB_SCI_TM_' + t_str + '.csv'
			self.files["fob_sci_tm"] = 'data\FOB_SCI_TM_' + t_str + '.csv'
			self.files["fsc_sci_tm"] = 'data\FSC_SCI_TM_' + t_str + '.csv'
			
	def update_hk_files(self, t_str): 
			self.files['fib_hk_tm'] = 'data\FIB_HK_TM_' + t_str + '.csv'
			self.files['fob_hk_tm'] = 'data\FOB_HK_TM_' + t_str + '.csv'
			self.files['fsc_hk_tm'] = 'data\FSC_HK_TM_' + t_str + '.csv'
			self.files['pcu_data'] = 'data\PCU' + t_str + '.csv'
			self.labels['fib_hk_tm'] = ['Time','Status_HB','Status_LB','LUP_cnt','P1V5','P3V3','P5V','N5V','P8V','P12V','P1I5','P3I3','P5I','N5I','P8I','P12I','TE','TS1','TS2','Checksum','CMD_exec_cnt','ICU_err_cnt','Last_cmd','Last_err','HK_req_cnt','sync_count']
			self.labels['fob_hk_tm']= ['Time', 'Delay/Advance Val', 'ICU packet checksum', 'ICU command count', 'sync_pulse_count']
			self.labels['fsc_hk_tm'] = ['Time', 'Peregrine_Lock','Sensor_Temp_A','Sensor_Temp_B','Sensor_Temp_Duty_Cycle','Laser_Temp_A','Laser_Temp_B','Laser_Temp_Duty_Cycle','Laser_Current','Laser_Current_Zero_Cross','Microwave_Ref','Microwave_Ref_Zero_Cross','Zeeman_Freq_Zero_Cross','PCB_Temp_A','PCB_Temp_B','Laser_Diode_Voltage','Diode_Optical_Power','P2V4','P3V3','P8V','N8V','P12V','PCB_Temp_C','PCB_Temp_D','PCB_Temp_E','ICU_Checksum','ICU_Command_Count','ICU_Sync_Count'] 
			self.labels['pcu_data'] = ['Time','I_FIB','I_FOB','I_FSC','I_P3V3','I_FIBH','I_FOBH','I_FSCH','I_P1V8','Temp','V_P2V4','V_P3V3','V_P12V','V_P8V','V_N8V','V_P5V','V_N5V']
			self.labels['fib_sci_tm'] = ['Time', 'Bx', 'By', 'Bz' 'status']
			self.labels['fob_sci_tm']  = ['Time', 'Bx', 'By', 'Bz' 'status']
			self.labels['fsc_sci_tm'] = ['Time',	'Sensor_Laser',	'Laser_Micro',	'Zeeman',	'Sci_Data_ID',	'Sci_Data',	'Timestamp']

	def run(self): 
		self.current_time = self.update_global_time()
		t_str = self.current_time.strftime("%Y%m%d_%H%M%S")
		self.update_hk_files(t_str)
		#a flag that has been to ensure that the thread is executing while the user wants it to
		for key in self.files:
			with open(self.files[key], 'a') as infile:  
				infile.write("{}\n".format(','.join(self.labels[key])))
				
		
		while self.start_running:
			while self.serial.inWaiting():
				decision_hk_sci = bytes(self.serial.read(size = 1))
				counter = int.from_bytes(self.serial.read(size = 4), byteorder = 'big')
				self.time = (self.current_time + datetime.timedelta(seconds = counter/128)).strftime("%Y%m%dT%H%M%S.%f")
				if(decision_hk_sci == b'\x01'): 
					for key in self.sci_values: 
						self.sci_values[key] = ''
						self.sci_values[key] = self.time + ','
					s = fee_science(self.time, self.serial, self.sci_values)
					for key in self.sci_values: 
						with open(self.files['fib_sci_tm'], 'a') as infile, open(self.files['fob_sci_tm'], 'a') as infile2, open(self.files['fsc_sci_tm'], 'a') as infile3: 
							if key == 'fib_sci_tm': 
								infile.write("{}\n".format(self.sci_values[key]))
							if key == 'fob_sci_tm':  
								infile2.write("{}\n".format(self.sci_values[key]))
							if key == 'fsc_sci_tm':  
								infile3.write("{}\n".format(self.sci_values[key]))

				elif(decision_hk_sci == b'\x00'):
					for key in self.hk_values: 
						self.hk_values[key] = ''
						self.hk_values[key] = self.time + ','
					h = hk_data(self.serial, self.hk_values)
					for key in self.hk_values: 
						with open (self.files['fib_hk_tm'], 'a') as infile, open(self.files['fob_hk_tm'], 'a') as infile2, open(self.files['fsc_hk_tm'], 'a') as infile3, open(self.files['pcu_data'], 'a') as infile4: 
							if key == 'fib_hk_tm': 
								infile.write("{}\n".format(self.hk_values[key]))
							if key == 'fob_hk_tm':  
								infile2.write("{}\n".format(self.hk_values[key]))
							if key == 'fsc_hk_tm':  
								infile3.write("{}\n".format(self.hk_values[key]))
							if key == 'pcu_data':  
								infile4.write("{}\n".format(self.hk_values[key]))
							
class fee_science():
		def __init__(self, time,  port, values): 
			header_data = port.read(size = 3)
			if(header_data[0] > 0): 
				fb = fib_sci(port.read(size = 10),  values)
			if(header_data[1] > 0): 
				fo = fob_sci(port.read(size = 10),  values)
			if(header_data[2] > 0): 
				fs = fsc_sci(port.read(size = 11),  values) 

class fib_sci(): 
		def __init__(self, data, values):  
			self.update(data, values) 
		def update(self, data, values): 
			for i in range(0, 3):
				values["fib_sci_tm"] += "{},".format(int.from_bytes(data[3*i : 3*i + 3], byteorder = 'big', signed = True))
				
			
class fob_sci(): 
		def __init__(self, data, values): 
			self.update(data, values)
		def update(self, data, values): 
			for i in range(0, 3):
				values["fob_sci_tm"] += "{},".format(int.from_bytes(data[3*i : 3*i + 3], byteorder = 'little', signed = True))
	

class fsc_sci():
		def __init__(self, data, values): 
			self.update(data, values)
		def update(self, data, values):
			for i in range (0, 4): 
				values["fsc_sci_tm"]  +=  "{},".format(int(data[i]))
			values["fsc_sci_tm"]  += "{},".format(int.from_bytes(data[4:8], byteorder = 'big', signed = False))
			values["fsc_sci_tm"]  += "{},".format(int.from_bytes(data[8:11], byteorder = 'big', signed = False))
						
						
class files(): 
		def __init__(name): 
			return open(name)
						

class pcu_data(): 
		def __init__(self, data,  values):
			self.update(data, values)
		def update(self, data,  values):
			for i in range(0, 32): 
				if (i % 2 == 0): 
					values["pcu_data"] += "{},".format(int.from_bytes(data[i:i+2], byteorder = 'big', signed = False))
class fib_hk_data():
		def __init__(self, data, values): 
			self.update(data,  values)
		def update(self, data, values):
			for i in range(0, 3):
				values["fib_hk_tm"] += "{},".format(int(data[i]))
			for i in range(1, 32):
				if(i % 2 == 0):
					values["fib_hk_tm"] += ("{},".format(int.from_bytes(data[(i + 2): (i + 4)], byteorder = 'big', signed = False)))
			for i in range(33, len(data)): 
				values["fib_hk_tm"] += "{},".format(int(data[i]))
class fob_hk_data():
		def __init__(self, data,  values): 
			self.update(data, values)
		def update(self, data, values): 
			for i in range(0, len(data)): 
				values["fob_hk_tm"] += "{},".format(int(data[i]))

class fsc_hk_data():
		def __init__(self, data, values): 
			self.update(data, values)
		def update(self, data, values): 
			values["fsc_hk_tm"] += "{},".format(int(data[0]))
			for i in range (0, 4): 
				if(i % 2 == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 1): (i + 3)], byteorder = 'big', signed = False))
			
			values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[5 : 7], byteorder = 'big', signed = False))
			
			for i in range(0, 4): 
				if(i % 2  == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 7): (i + 9)], byteorder = 'big', signed = False))
			
			values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[11: 13], byteorder = 'big', signed = False))
			
			for i in range(0, 6): 
				if(i % 3 == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 13): (i + 16)], byteorder = 'big', signed = False))
			
			for i in range(0, 4): 
				if(i % 2 == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 19):(i + 21)], byteorder = 'big', signed = False))
		
			values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[23:26], byteorder = 'big', signed = False))
			
			for i in range (0, 4): 
				if(i % 2 == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 26) : (i + 28)], byteorder = 'big', signed = False))
				
			values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[30 : 32], byteorder = 'big', signed = False))
			values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[32: 34], byteorder = 'big', signed = False))
			
			for i in range(0, 16): 
				if (i % 2 == 0): 
					values["fsc_hk_tm"] += "{},".format(int.from_bytes(data[(i + 34) : (i + 36)], byteorder = 'big', signed = False))
					
			for i in range(48, 51): 
				values["fsc_hk_tm"] += "{},".format(int(data[i]))
		
if __name__ == '__main__':
		parser = argparse.ArgumentParser();
		parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
		parser.add_argument('--abs_path', dest = 'abs_path', help = "check for absolute directory", type = str)
		args 	 = parser.parse_args()
		logging.basicConfig(filename='debugger.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
		logger = logging.getLogger()
		switch_off = False
		logger.setLevel(logging.INFO) 
		
		pkt_reciever = packet_reciever(parser.parse_args().port, parser.parse_args().abs_path)
		pkt_reciever.start() 
		while not pkt_reciever.is_alive(): 
			pass 
		time.sleep(2)
		## needed as arduino needs to come up, do not remove. 
		cmd_menu 	= (	"1) Set Time Command \n"
						"2) Set Config Command \n"
						"3) Science Mode \n"
						"4) Config Mode \n"
						"5) Power on fee \n"
						"6) Power off fee \n"
						"7) End the script \n")
						
		fee_number 	= (	"0> FIB \n"
						"1> FOB \n"
						"2> FSC \n")
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
			if choice == 2: 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big') + build_config_command_val(fee_number));
			elif choice == 4:
				command = ((int(nb, 16).to_bytes(1, byteorder = 'big'))); 
			elif(nb == '3'):
				pkt_reciever.begin_receiving = True
				pkt_reciever.update_sci_files(pkt_reciever.current_time.strftime("%Y%m%d_%H%M%S"))
				for key in pkt_reciever.files:
					with open (pkt_reciever.files[key], 'a') as infile:  
						infile.write("{}\n".format(','.join(pkt_reciever.labels[key])))
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big'))
			elif(nb == '5' or nb == '6'): 
				command = ((int(nb, 16)).to_bytes(1, byteorder = 'big')) + build_fee_packet(fee_number) 
			elif(nb == '7'): 
				pkt_reciever.start_running = False
				switch_off = True
			if(nb != '7' and pkt_reciever.is_alive() == True):
					pkt_reciever.serial.write(bytes(command));
			print(command)	
		pkt_reciever.join()
		print("program end")


