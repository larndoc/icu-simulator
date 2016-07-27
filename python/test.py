import serial 
import argparse
import string
import time 
import datetime

if __name__ == "__main__":
	# args = parser.parse_args() 
	# port = args.port 
	# serial_port = serial.Serial(port, baud_rate, timeout = 1)
	# send_start_command_to_arduino(serial_port)
	# while 1: 
		# try: 	
			# with open((file_name[1]), "a") as f: 
					# f.write("fsc_sci_" + timestr)
		# except serial.SerialTimeoutException:
			# print("DATA COULD NOT BE READ")  
	
	parser = argparse.ArgumentParser();
	parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
	args = parser.parse_args() 
	
	s = serial.Serial(args.port, 115200, timeout = 0.5)
	
	# arduino startup time
	time.sleep(1)
	science_data = [0, 0, 0]
	x_hb = [0, 0, 0]
	y_hb = [0, 0, 0]
	z_hb = [0, 0, 0]
	t = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
	s.write(b'5')
	with open("fib_sci_" + t + ".csv", 'a') as f, open ("fob_sci_" + t + ".csv", 'a') as se,  open ("fsc_sci_" + t + ".csv", 'a') as d:
		f.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		d.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		se.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		current_time = datetime.datetime.now()
		while True:
			try:
				data = s.read(size = 18)
				s.flushInput()
				status = str(data[0]);
				
				fib_lower_limit = 8; 
				fib_upper_limit = fib_lower_limit + 10*data[5] - 1; 
				if(fib_lower_limit < fib_upper_limit):
					science_data[0] = ("{}".format(int.from_bytes(data[fib_lower_limit:fib_upper_limit], 'little')))
					
				fob_lower_limit = fib_lower_limit + 10*data[5] 
				fob_upper_limit = fib_lower_limit + 10*data[5] + 10*data[6] - 1;
				if(fob_lower_limit < fob_upper_limit): 
					science_data[1] = ("{}".format(int.from_bytes(data[fob_lower_limit:fob_upper_limit], 'little')))
				
				fsc_lower_limit = fob_upper_limit + 1
				fsc_upper_limit = fsc_lower_limit + 10*data[7]  - 1; 
				if(fsc_lower_limit < fsc_upper_limit): 
					science_data[2] = ("{}".format(int.from_bytes(data[fsc_lower_limit:fsc_upper_limit], 'little')))
	
				for i in range(0, 3):
					if(data[i+5] > 0 ): 
						x_hb[i] = int(science_data[i]) & 0x00000001
						y_hb[i] = int(science_data[i]) & 0x00000003
						z_hb[i] = int(science_data[i]) & 0x00000006
				
				if(data[0] > 0):
					f.write(status + "," + current_time.strftime("%Y-%m-%d")  + " , "  + current_time.strftime("%H:%M:%S.%f") +  "," + ("{}".format(int.from_bytes(data[1:5], byteorder  = 'little'))) + "\n") 
				if(data[1] > 0):
					d.write(status + "," + current_time.strftime("%Y-%m-%d")  + " , " + current_time.strftime("%H:%M:%S.%f") +  ", " + ("{}".format(int.from_bytes(data[1:5], byteorder = 'little'))) + "\n") 
				if(data[2] > 0):
					se.write(status + "," + current_time.strftime("%Y-%m-%d") + " , " + current_time.strftime("%H:%M:%S.%f") +  ", " + ("{}".format(int.from_bytes(data[1:5], byteorder = 'little'))) + "\n")
				
				current_time = current_time + datetime.timedelta(milliseconds = 7.8125)					#frequency set at 128 Hz, timedelta = 1/frequency ~ 7.8125 milliseconds
			except KeyboardInterrupt:
				break;

			
			
	
	
		
	
	