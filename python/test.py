import serial 
import argparse
import string
import time 
import datetime

if __name__ == "__main__":
	#initialization of the baud rate 
	#initialization of the argument parser for the user to enter the desired communication port 
	#initialization of the science data and the x, y and z components from all 3 interfaces 
	#setting up the communication via the usb interface with a timeout of 0.5 seconds 
	baud_rate = 115200 
	parser = argparse.ArgumentParser();
	parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
	args = parser.parse_args() 
	science_data = [0, 0, 0]
	x_hb = [0, 0, 0]
	y_hb = [0, 0, 0]
	z_hb = [0, 0, 0]
	
	s = serial.Serial(args.port, baud_rate, timeout = 1)
	
	# arduino startup time
	time.sleep(1)

	
	#timestamp for each of the filenames
	t  = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
	
	#sending start command to the arduino 
	s.write(b'5')
	
	#opening all the 3 files with the time_stamp 
	with open("fib_sci_" + t + ".csv", 'a') as f, open ("fob_sci_" + t + ".csv", 'a') as se,  open ("fsc_sci_" + t + ".csv", 'a') as d:
		f.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		d.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		se.write("status" + "," + "date" + "," +  "time" + "," +  "sync_counter" + "\n")
		current_time = datetime.datetime.now()
		while True:
			try:
				data = s.read(size = 18)
				s.flushInput()
				#print(data[7])
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
						print("current index" + str(i + 1)  +  " " + str(x_hb[i]) + " " + str(y_hb[i]) + " " + str(z_hb[i]))
				if(data[5] > 0):
					f.write(status + "," + current_time.strftime("%Y-%m-%d")  + " , "  + current_time.strftime("%H:%M:%S.%f") +  "," + ("{}".format(int.from_bytes(data[1:5], byteorder  = 'little'))) + "\n") 
				if(data[6] > 0):
					d.write(status + "," + current_time.strftime("%Y-%m-%d")  + " , " + current_time.strftime("%H:%M:%S.%f") +  ", " + ("{}".format(int.from_bytes(data[1:5], byteorder = 'little'))) + "\n") 
				if(data[7] > 0):
					se.write(status + "," + current_time.strftime("%Y-%m-%d") + " , " + current_time.strftime("%H:%M:%S.%f") +  ", " + ("{}".format(int.from_bytes(data[1:5], byteorder = 'little'))) + "\n")
				
				current_time = current_time + datetime.timedelta(milliseconds = 7.8125)					#frequency set at 128 Hz, timedelta = 1/frequency ~ 7.8125 milliseconds
			except KeyboardInterrupt:
				break;

			
			
	
	
		
	
	