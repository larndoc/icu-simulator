# plot power spectral density of the sawtooth waveform?
# plot frequency sprectrum of the sawtooth waveform?

import serial
import argparse
import string
import time
import datetime
import binascii
import logging
import numpy
import statistics
from threading import Thread
import math
import os

# these are the number of bits in the x, y and z coordinates in the fib file.
number_of_bits_coordinates_fib = [24, 24, 24]
number_of_bits_coordinates_fob = [24, 24, 24]


# wrap this inside a function
def init_debug_logger():



start_science = True
recieve_serial = True
switch_off = False


def build_config_command_val(fee_number):
    print(fee_number)
    cmd = input('> please choose an input: ')
    cmd_val = (int(cmd, 0)).to_bytes(1, byteorder='big')
    read_write = (
        "0) read \n"
        "1) write \n"
    )
    print(read_write)
    rm_wr = input('> please choose an input: ')
    rm_wr_val = (int(rm_wr, 0)).to_bytes(1, byteorder='big')
    config_id = input('>please enter config id: ')
    config_id_val = (int(config_id, 0)).to_bytes(1, byteorder='big')
    config_val = input('>please enter config val: ')
    temp = int(config_val, 0)
    choice = (temp).to_bytes(3, byteorder='big')
    return cmd_val + rm_wr_val + config_id_val + choice


def build_fee_packet(fee_number):
    print(fee_number)
    fee_interface = input('please choose an input: ')
    return (int(fee_interface, 0)).to_bytes(1, byteorder='big')


def debug_information(data):
    print(binascii.hexlify(data))


def minute_tick(current_minutes, old_minutes):
    if (current_minute != old_minutes):
        old_minutes = current_minute
        return True
    else:
        return False


class packet_reciever(Thread):
    # initialization of the baud rate
    # initialization of the argument parser for the user to enter the desired communication port
    # initialization of the science data and the x, y and z components from all 3 interfaces
    # setting up the communication via the usb interface with a timeout of 0.5 seconds
    # the print function messes with the data that is being printed on the console
    # s = serial.Serial('COM4', 115200, timeout = 1)
    def __init__(self, serial_port, logdir):
        super(packet_reciever, self).__init__()
        self._port = serial_port
        self._logdir = logdir
        self._active = True

        self.sci_files = dict()
        self.fee_sci_labels = dict()
        self.fee_sci_labels["fib"] = ['Time', 'Bx', 'By', 'Bz', 'status']
        self.fee_sci_labels["fob"] = ['Time', 'Bx', 'By', 'Bz', 'status']
        self.fee_sci_labels["fsc"] = ['Time', 'Ctr_T', 'Ctr_L', 'Sci_ID', 'data', 't']

        # open files in the beginning only (simple) - could be changed later on
        self.open_files()


    def open_files(self):
        """ Opens files for writing to (e.g. Sci files)
        :return:
        """
        t_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # for simplicity now, we could change that if we wanted
        self.sci_files["fib"] = open(self._logdir + '/FIB_Sci_TM' + t_str + '.csv')
        self.sci_files["fob"] = open(self._logdir + '/FOB_Sci_TM' + t_str + '.csv')
        self.sci_files["fsc"] = open(self._logdir + '/FSC_Sci_TM' + t_str + '.csv')
        # write first line in the files with labels
        for key, f in self.sci_files.items():
            f.write(",".join(self.fee_sci_labels))

    def parse_fee_sci(self, fee):
        """Parses the serial port for a science packet of an fee
        :param fee: the fee science packet to parse (string), e.g. 'fib'
        :return: returns a list of parsed values (integers)
        """

        values = []
        if fee=='fib':
            sci_data = self._port.read(size=10)
            # append x, y, z values
            for i in range(0,3):
                values.append(int.from_bytes(sci_data[3*i:3*i+3], byteorder='big', signed=True))
            # append status byte
            values.append(sci_data[9])
        elif fee=='fob':
            sci_data = self._port.read(size=10)
            # append x, y, z values
            for i in range(0,3):
                values.append(int.from_bytes(sci_data[3*i:3*i+3], byteorder='big', signed=True))
            # append status byte
            values.append(sci_data[9])
        elif fee=='fsc':
            sci_data = self._port.read(size=11)
            values.append(sci_data[0])
            values.append(sci_data[1])
            values.append(sci_data[2])
            values.append(sci_data[3])
            values.append(int.from_bytes(sci_data[4:8], byteorder='big', signed=False))
            values.append(int.from_bytes(sci_data[9:11], byteorder='big', signed=False))
        return values


    def parse_sci(self):
        """Parses the serial port for a science packet
        :return: a dict of parsed science packets with keys being "fib/fob/fsc"
        """
        header = self._port.read(size=7)
        counter = int.from_bytes(header[0:4], byteorder='big')
        n = dict(fib=0, fob=0, fsc=0)
        parsed = dict(fib="", fob="", fsc="")
        n["fib"].append(header[4])
        n["fob"].append(header[5])
        n["fsc"].append(header[6])

        # get the timestamp of the data
        t = self.time_reference + datetime.timedelta(seconds=counter/128)

        for key in parsed:
            for n in n[key]:
                values = self.parse_fee_sci(key)
                parsed[key].append("{:s},{:s}\n".format(t.strftime("%Y%m%dT%H:%M:%S.%f"),",".join(str(values))))

        return parsed

    def parse_hk(self):
        pass

    def run(self):
        # arduino startup time
        # timestamp for each of the filenames
        while self._active == True:
            # receive one byte
            b = self._port.read(size=1)
            if len(b) > 0:
                # we received something
                if b[0] == b'\x00':
                    # it's a housekeeping packet
                    self.parse_hk() #@ASAD: write this function similar to parse_sci()
                elif b[0] == b'\x01':
                    # it's a science packet
                    parsed = self.parse_sci()
                    # write it
                    for key, value in parsed.items():
                        self.sci_files[key].write(value)
                else:
                    # something else received
                    raise IOError("Serial port reading failed")

    def capture_time(self):
        """Captures the current time as reference point. """
        self.time_reference = datetime.datetime.now()

    def close(self):
        """Closes the object (and files associated)
        """
        self._active = False
        for key, f in self.sci_files:
            f.close()


if __name__ == '__main__':

    # config logger
    logging.basicConfig(filename='debugger.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # config parser
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='port', help="serial port of the ICU Simulator unit", type=str)
    parser.add_argument('--logdir', dest='logdir', help="path to store data files", type=str)
    args = parser.parse_args()

    # config serial port
    s = serial.Serial(args.port, 115200, timeout=0.5)

    # create serial packet handler
    packet_handler = packet_reciever(s, args.logdir)
    packet_handler.start()
    while not packet_handler.is_alive():
        pass

    time.sleep(2)

    # so here we assume the ICU has started counting
    packet_handler.capture_time()

    ## needed as arduino needs to come up, do not remove.
    cmd_menu = ("1) Set Time Command \n"
                "2) Set Config Command \n"
                "3) Science Mode \n"
                "4) Config Mode \n"
                "5) Power on fee \n"
                "6) Power off fee \n"
                "7) End the script \n")
    fee_number = ("0> FIB \n"
                  "1> FOB \n"
                  "2> FSC \n")
    command = ''

    # continue to stay in the loop until the user wants to exit the script in which case we must end the thread
    while (switch_off == False):
        print(cmd_menu)
        nb = input('please choose an option: ')
        try:
            choice = int(nb)
        except ValueError as error_msg:
            print('unable to parse choice as an integer %s' % error_msg)
            logging.debug(error_msg)
            continue
        if (nb == '2'):
            command = ((int(nb, 16)).to_bytes(1, byteorder='big') + build_config_command_val(fee_number))
        elif (nb == '4'):
            command = ((int(nb, 16).to_bytes(1, byteorder='big')))
        elif (nb == '3'):
            packet_handler.start_science = True
            command = ((int(nb, 16)).to_bytes(1, byteorder='big'))
        elif (nb == '5' or nb == '6'):
            command = ((int(nb, 16)).to_bytes(1, byteorder='big')) + build_fee_packet(fee_number)
        elif (nb == '7'):
            packet_handler.close()
            switch_off = True
        if (nb != '7' and packet_handler.is_alive() == True):
            s.write(bytes(command));
        print(command)
    packet_handler.join()
    print("program end")


# heat map
# rate of change of x, y and z with respect to time
# moving averages
# auto correlation
# confidence interval
# power spectral desnity
# frequency spectrum
