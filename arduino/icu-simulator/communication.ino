  #include "pc_data_dump.h"
  #define CMD_PACKET_SIZE 6 
   uint8_t default_fee_cmd[CMD_PACKET_SIZE] = {0x01, 0x00, 0x00, 0x00, 0x00, 0x01}; 
   uint8_t fee_cmd[3][CMD_PACKET_SIZE]; 
   uint8_t *cmd_packet[3] = {default_fee_cmd, default_fee_cmd, default_fee_cmd};
  
  void process_packet(uint8_t index){                                                     //on every sync signal check to see if there is some processing to do and send the UART packet to the rest of the interfaces respectively. 
      check_checksum(index); 
      if(response_packet_counter[index] > 0){
      packet_exists[index] = true;
      }
      response_packet_counter[index] = 0; 

      global_packet_counter[index]++; 
      
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
      if(buffer_index == BUFFER_SIZE - 1){
                write_command = true; 
              }
      fee_packet[index][buffer_index].arr[response_packet_counter[index]] = port->read(); 
      checksum[index] ^= fee_packet[index][buffer_index].arr[response_packet_counter[index]]; 
      response_packet_counter[index]++;  
      if(response_packet_counter[index] > FEE_PACKET_SIZE){
                                                               //if packet size exceeds the maximum fee_packet_size then set the flag, i.e set pin 10 HIGH and continue mode of operation
      }
    }
  }
