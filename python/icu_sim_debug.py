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
    cmd_val = (int(cmd, 0)).to_bytes(1, byteorder='big')
    read_write = (
        "0) read \n"
        "1) write \n"
    )
    print(read_write)
    rm_wr = input('> please choose an input: ')
    rm_wr_val = int(rm_wr, 0).to_bytes(1, byteorder='big')
    config_id = input('>please enter config id: ')
    config_id_val = int(config_id, 0).to_bytes(1, byteorder='big')
    config_val = input('>please enter config val: ')
    choice = int(config_val, 0).to_bytes(3, byteorder='big')
    return cmd_val + rm_wr_val + config_id_val + choice


def build_fee_packet(fee_number):
    print(fee_number)
    fee_interface = input('please choose an input: ')
    return int(fee_interface, 0).to_bytes(1, byteorder='big')


class hk_data:
    def __init__(self, port):
        self.port = port

    def update(self):
     values = b''
     hk_packets = [self.port.read(size=32), self.port.read(size=40), self.port.read(size=4), self.port.read(size=53)]
     for i in range(0, 4):
         values+= hk_packets[i]
     return binascii.hexlify(values).decode()


class packet_reciever(Thread):
    # recieves a packet and reads the first byte
    hk_values = dict()
    sci_values = dict()
    files = dict()
    start_running = True

    def __init__(self, serial_port, logdir):
        super(packet_reciever, self).__init__()
        self.port = serial_port
        self.logdir = logdir
        self.serial = self.set_up_serial()

    def set_up_serial(self):
        return serial.Serial(self.port, 115200, timeout=0.5)

    def update_global_time(self):
        return datetime.datetime.now()

    def update_files(self):
        self.files = {'fee_sci_tm': 'data/fee_science.log', 'house_keeping': 'data/hk.log'}

    def run(self):
        self.update_files()
        s = fee_science(self.serial)
        h = hk_data(self.serial)
        values = [self.hk_values, self.sci_values]
        while self.start_running:
            while self.serial.inWaiting():
                decision_hk_sci = bytes(self.serial.read(size=1))
                if decision_hk_sci[0] == 0:
                    print('a')
                    with open(self.files['house_keeping'], 'a') as f: 
                        f.write("00" + h.update() + "\n")
                    #values[0]['house_keeping'] = decision_hk_sci
                    #h.update(values[0])
                elif decision_hk_sci[0] == 1:
                    with open(self.files['fee_sci_tm'],'a') as f:
                        f.write("01" + s.update() + "\n")


class fee_science():
    def __init__(self, port):
        self.port = port

    def update(self):
        values = b""
        values += self.port.read(size=4)
        n_fee = self.port.read(size=3)
        values += n_fee
        for i in range(0, n_fee[0]):
            values += self.port.read(size=10)

        for i in range(0, n_fee[1]):
            values += self.port.read(size=10)

        for i in range(0, n_fee[2]):
            values += self.port.read(size=11)
        return binascii.hexlify(values).decode()


if __name__ == '__main__':
    logging.basicConfig(filename='debugger.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger()
    switch_off = False
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser();
    parser.add_argument(dest='port', help="serial port of the ICU Simulator unit", type=str)
    parser.add_argument('--logdir', dest='logdir', help="path to store data files", type=str)
    args = parser.parse_args()

    pkt_reciever = packet_reciever(parser.parse_args().port, parser.parse_args().logdir)
    pkt_reciever.start()
    while not pkt_reciever.is_alive():
        pass
    time.sleep(2)
    ## needed as arduino needs to come up, do not remove.
    ## should update the global time here as it is more readable


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
    while (switch_off == False):
        print(cmd_menu)
        nb = input('please choose an option: ')
        try:
            choice = int(nb)
        except ValueError as error_msg:
            print('unable to parse choice as an integer %s' % error_msg)
            logging.debug(error_msg)
            continue
        if choice == 2:
            command = ((int(nb, 16)).to_bytes(1, byteorder='big') + build_config_command_val(fee_number));
        elif choice == 4:
            command = ((int(nb, 16).to_bytes(1, byteorder='big')));
        elif choice == 3:
            pkt_reciever.begin_receiving = True
            command = ((int(nb, 16)).to_bytes(1, byteorder='big'))
        elif choice == 5 or choice == 6:
            command = ((int(nb, 16)).to_bytes(1, byteorder='big')) + build_fee_packet(fee_number)
        elif choice == 7:
            pkt_reciever.start_running = False
            switch_off = True
        if choice != 7 and pkt_reciever.is_alive() == True:
            pkt_reciever.serial.write(bytes(command));
        print(command)
    pkt_reciever.join()
    print("program end")