  #include "pc_data_dump.h"
 void update_command(int index)
 {
    for(int i = 0; i < 6; i++)
    {
      cmd_packet[index][i] = 0; 
    }
    cmd_packet[index][0] = 1; 
    cmd_packet[index][5] = 1; 
 }

 
  void process_packet(uint8_t index){                                                     //on every sync signal check to see if there is some processing to do and send the UART packet to the rest of the interfaces respectively. 
      check_checksum(index); 
      if(response_packet_counter[index] > 0){
      packet_exists[index] = true;
      }
      response_packet_counter[index] = 0; 

      global_packet_counter[index]++; 
      
  }




  void send_packet(HardwareSerial* port, int index)
  {
     /*cmd_packet[index][0] is the first byte of the icu packet, if it is set to 5 or 7 then it means we sent a command to change how icu packet is assembled, if change_command_packet is false, it means that this upgrade did not complete */
        if(cmd_packet[index][0] == 5 || cmd_packet[index][0] == 3){
            port->write(cmd_packet[index], PACKET_SIZE); 
        }
        else{
          port->write(cmd_packet[index], PACKET_SIZE); 
        }
        //set the icu command packet to 1000001; 
        update_command(index); 
   }
 
  
  void check_port(HardwareSerial* port, int index){
    if(port->available()){
      fee_packet[index].arr[response_packet_counter[index]] = port->read(); 
      checksum[index] ^= fee_packet[index].arr[response_packet_counter[index]]; 
      response_packet_counter[index]++;  
      if(response_packet_counter[index] > FEE_PACKET_SIZE){
                                                               //if packet size exceeds the maximum fee_packet_size then set the flag, i.e set pin 10 HIGH and continue mode of operation
      }
    }
  }
