import serial 
import argparse
import string
import time 
import base64
def send_start_command_to_arduino(serial_port): 
	time_out = 1
	time.sleep(time_out)
	serial_port.setDTR(0)
	serial_port.write(b'5')
	time.sleep(time_out)
	
	
if __name__ == "__main__":
	baud_rate = 250000 
	created = {false, false, false }
	file = open("newfile.csv", 'w')
	file.write("hello world in another line")
	parser = argparse.ArgumentParser(); 
	parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
	args = parser.parse_args() 
	port = args.port 
	serial_port = serial.Serial(port, baud_rate, timeout = 1)
	send_start_command_to_arduino(serial_port)
	while 1: 
		try: 	
			data = (serial_port.read(size = 1))
			if(data[0] == 1 && created[0] == false):
				string file = "sci_fib"
				created[0] = true
				with open(file, "w") as f: 
					f.write("HELLO")
			print(data)
		except serial.SerialTimeoutException:
			print("DATA COULD NOT BE READ")  
	