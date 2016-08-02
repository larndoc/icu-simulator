import serial
import module

if __name__ == "__main__":
	while True: 
		module.nb = input('please choose a command: ')
		if (module.nb == 'A'): 
			encoded = module.nb.encode('utf-8')
			module.s.write(encoded)
		elif(module.nb == '5'): 
			encoded = module.nb.encode('utf-8')
			module.s.write(encoded)