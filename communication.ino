  #include "test.h"
  #include "packets.h" 

  void process_packet(union fee_paket* fee_ptr, uint8_t index){
    if(packet_exists[index]){
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
  
  bool check_capacity(int crt_pckt_size)
  {
    if (crt_pckt_size > FEE_PACKET_SIZE){
      //do something 
       return true; 
    }
    else{
      return false; 
    }
  }
  void check_port(HardwareSerial* port, int index){
    if(port->available()){
      packet_exists[index] = true; 
      fee_packet_ptr[index]->arr[response_packet_counter[index]] = port->read(); 
      checksum[index] ^= fee_packet_ptr[index]->arr[response_packet_counter[index]]; 
      response_packet_counter[index]++;  
    }
  }
  
  void recieve_reply()
  {
    for(int i = 0; i < 3; i++){
      check_port(port[i], i); 
    } 
  }
  
  bool set_flag(int index){
    if(check_capacity[index]){ 
      //digitalWrite(13, HIGH); 
      //response_packet_counter[index] = 0; 
      check_cap[index] = true;
    } 
  }

