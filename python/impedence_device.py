from abc import ABCMeta, abstractmethod

class fee_packet: 
	def update(self, id, time, n_fib, n_fob, n_fsc):
		self.__id = id
		self.__time = time
		self.__n_fib = n_fib
		self.__n_fob = n_fob
		self.__n_fsc = n_fsc 
	#@abstractmethod
	def store_to_pc(self, file): 
		print(self.id + "," + self.time + "," + self.n_fob + "," + self.n_fsc + ",")

class fsc_packet(fee_packet):
	def update(self, id, time, n_fib, n_fob, n_fsc, byte_0, byte_1, byte_2, byte_3, science_data, time_stamp):
		fee_packet.update(self, id, time, n_fib, n_fob, n_fsc)
		self.__sensor_temp_controller 			= byte_0 & 0xF0
		self.__laser_temp_controller  			= byte_0 & 0x0F
		self.__laser_current_controller 		= byte_1 & 0xF0 
		self.__microwave_reference_controller 	= byte_1 & 0x0F
		self.__zeeman_controller 				= byte_2
		self.__science_data_id 					= byte_3
		self.__science_data						= science_data 
		self.__time_stamp						= time_stamp
		
	def store_to_pc(self, file): 
		fee_packet.store_to_pc(self, file)
		print(self.sensor_temp_controller + "," + self.laser_temp_controller + "," + self.laser_current_controller + "," + self.microwave_reference_controller + "," +  self.zeeman_controller + "," + self.science_data_id +  "," + self.science_data + "," self.time_stamp); 


class fib_packet(fee_packet):
	def update(self, id, time, n_fib, n_fob, n_fsc, x_hb, x_mb, x_lb, y_hb, y_mb, y_lb, z_hb, z_mb, z_lb): 
		fee_packet.update(self, id, time, n_fib, n_fob, n_fsc)
		x_arr[3] = [x_hb, x_mb, x_lb]
		y_arr[3] = [y_hb, y_mb, y_lb] 
		z_arr[3] = [z_hb, z_mb, z_lb]
		self.__x =   ("{}".format(int.from_bytes(x_arr[0:3], byteorder = 'big')))
		self.__y =   ("{}".format(int.from_bytes(y_arr[0 : 3], byteorder = 'big')))
		self.__z =   ("{}".format(int.from_bytes(z_arr[0 : 3], byteorder = 'big')))
	
	def store_to_pc(self, file): 
		fee_packet.store_to_pc(self, file)
		print(self.x + "," + self.y + "," + self.z)






class employee:
	def __init__(self, name, status): 
		self.__name = name
		self.__status = status
	def get_value(self): 
		return self.__name
	def get_value_status(self): 
		return self.__status 
	def set_value(self, value): 
		self.__name = value
	@abstractmethod
	def printer(self):
		print("H")

		
class em(employee): 
	def __init__(self, name, status, date, data): 
		employee.__init__(self, name, status)
		self.__date = date 
		self.__data = data
	def update(self, value): 
		employee.set_value(self, value);
	def printer(self): 
		print(self.get_value())

class bm(employee): 
	def printer(self): 
		print("BYE")
		

if __name__ == '__main__':
	employeeList = [] 
	while(1):
		nb = input('Choose a input: ')
		if(nb == 'M'): 
			M = em('Ben', 'Withers', '1995-06-2015', '0x90')
			M.update("VALENCE")
			employeeList.append(M)
			M.printer()
		elif(nb == 'C'): 
			employeeList.append(bm('Lucy', 'Withers'))	
		