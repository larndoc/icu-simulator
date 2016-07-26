  #include "packets.h" 
  #include "pc_data_dump.h"
  
  void process_packet(union fee_paket* fee_ptr, uint8_t index){
    if(packet_exists[index]){
      pc_packet_ptr->time1 = sync_counter;
      print_packet(fee_ptr, index);                                                       //on every sync signal check to see if there is some processing to do and send the UART packet to the rest of the interfaces respectively. 
      check_checksum(fee_ptr, index); 
      packet_exists[index] = false; 
      response_packet_counter[index] = 0; 
      global_packet_counter[index]++; 
    }
  }

  void send_packet(HardwareSerial* port, int index)
  {
    if(!packet_exists[index] && fee_enabled[index]){
      port->write(cmd_packet, PACKET_SIZE); 
    }
  }
  
  void check_port(HardwareSerial* port, int index){
    if(port->available()){
      packet_exists[index] = true; 
      fee_packet_ptr[index]->arr[response_packet_counter[index]] = port->read(); 
      checksum[index] ^= fee_packet_ptr[index]->arr[response_packet_counter[index]]; 
      response_packet_counter[index]++;  
      if(response_packet_counter[index] > FEE_PACKET_SIZE){
        digitalWrite(led_pin, HIGH);                                                       //if packet size exceeds the maximum fee_packet_size then set the flag, i.e set pin 10 HIGH and continue mode of operation
      }
    }
  }
