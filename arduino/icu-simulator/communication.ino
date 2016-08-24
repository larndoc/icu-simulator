#include "pc_data_dump.h"
  #define CMD_PACKET_SIZE 6 
   uint8_t default_fee_cmd[CMD_PACKET_SIZE] = {0x01, 0x00, 0x00, 0x00, 0x00, 0x01}; 
   uint8_t fee_cmd[3][CMD_PACKET_SIZE]; 
   uint8_t *cmd_packet[3] = {default_fee_cmd, default_fee_cmd, default_fee_cmd};
  
  
  void create_pc_packet(int index){
    if(index == 0){
     pc_packet_arr[5] = BUFFER_SIZE;
      for(int l = 0; l < 10; l++, size_of_pc_packet++){
        pc_packet_arr[size_of_pc_packet] = fib_pack.science_data[l];
      }
    }
    if(index == 1){
     pc_packet_arr[6] = BUFFER_SIZE; 
      for(int l = 0; l < 10; l++, size_of_pc_packet++){
        pc_packet_arr[size_of_pc_packet] = fob_pack.science_data[l];
      }
     }

    if(index == 2){
     pc_packet_arr[7] = BUFFER_SIZE; 
      for(int l = 0; l < 11; l++, size_of_pc_packet++){
        pc_packet_arr[size_of_pc_packet] = fsc_pack.science_data[l];
      }
  }
  
  }
 
 
  void process_packet(uint8_t index){                                                     //on every sync signal check to see if there is some processing to do and send the UART packet to the rest of the interfaces respectively. 
      if(response_packet_counter[index] > 0){
        create_pc_packet(index);  
        response_packet_counter[index] = 0; 
  }
  }

  void create_cmd_packet(uint8_t * command){
    uint8_t index = command[0]; 
    cmd_packet[index] = fee_cmd[index]; 
    fee_cmd[index][0] = 0x00; 
    if(command[1] == 0){
      fee_cmd[index][0] |= 0x03;
    }
    else if(command[1] == 1){
      fee_cmd[index][0] |= 0x05;
    }
    fee_cmd[index][1] = command[2];
    fee_cmd[index][2] = command[3];
    fee_cmd[index][3] = command[4]; 
    fee_cmd[index][4] = command[5];
    fee_cmd[index][5] = 0; /*here we will build our checksum */
    for(int i = 0; i < 5; i++){
      fee_cmd[index][5] ^= fee_cmd[index][i];
    }
  }



  void send_packet(HardwareSerial* port, int index)
  {
     /*cmd_packet[index][0] is the first byte of the icu packet, if it is set to 5 or 7 then it means we sent a command to change how icu packet is assembled, if change_command_packet is false, it means that this upgrade did not complete */
        port->write(cmd_packet[index], CMD_PACKET_SIZE);
        //set the icu command packet to 1000001; 
        cmd_packet[index] = default_fee_cmd;
   }
 
  
  void check_port(HardwareSerial* port, int index){
    if(port->available() > 0){
      if(index == 2){
          fsc_pack.arr[response_packet_counter[2]] = port->read();
          checksum[index] ^= fsc_pack.arr[response_packet_counter[2]]; 
          response_packet_counter[2]++;  
      }
      
      if(index == 1){
          fob_pack.arr[response_packet_counter[1]] = port->read(); 
          checksum[1] ^= fob_pack.arr[response_packet_counter[1]]; 
          response_packet_counter[1]++;
      }
      if(index == 0){
          fib_pack.arr[response_packet_counter[0]] = port->read(); 
          checksum[0] ^= fib_pack.arr[response_packet_counter[0]]; 
          response_packet_counter[0]++;
      }
    }
  }
