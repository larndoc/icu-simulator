import serial 
import argparse
import string
import time 
import base64
def send_start_command_to_arduino(serial_port): 
	time_out = 1
	time.sleep(time_out)
	serial_port.setDTR(0)
	time.sleep(time_out)
	serial_port.write(b'5')
	serial_port.flushInput()
	time.sleep(time_out)
	
	
if __name__ == "__main__":
	baud_rate = 250000 
	parser = argparse.ArgumentParser(); 
	parser.add_argument(dest = 'port', help = "display the interface port to the computer ", type = str)
	args = parser.parse_args() 
	port = args.port 
	serial_port = serial.Serial(port, baud_rate, timeout = 1)
	send_start_command_to_arduino(serial_port)
	while 1: 
		try: 	
			if(serial_port.read != ''):
				print (serial_port.read(size = 7))
		except serial.SerialTimeoutException:
			print("DATA COULD NOT BE READ")  
	