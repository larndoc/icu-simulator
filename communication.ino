  #include "test.h"
  #include "packets.h" 
  void initiate_communication(){
      Serial.begin(250000); 
      Serial1.begin(BAUD_RATE); 
      Serial2.begin(BAUD_RATE); 
      Serial3.begin(BAUD_RATE); 
  }

  void process_packet(uint8_t* fee_ptr, uint8_t index){
    if(packet_exists[index]){
      print_packet(fee_ptr, index);                                                       //on every sync signal check to see if there is some processing to do and send the UART packet to the rest of the interfaces respectively. 
      check_checksum(fee_ptr, index); 
      packet_exists[index] = false; 
      response_packet_counter[index] = 0; 
      global_packet_counter[index]++; 
    }
    
  }
  
  void serial_write(bool send_cmd[3]){  
    process_packet(fee_packet_ptr[0], 0);                                           //on every rising edge we will first check to see if a packet exists and proces it accordingly, re-initialzing the flag to false and the counter to its initial value
    process_packet(fee_packet_ptr[1], 1); 
    process_packet(fee_packet_ptr[2], 2); 
    if(!packet_exists[0] && send_cmd[0]){ 
        Serial1.write(cmd_packet, PACKET_SIZE);                                     //if the packet doesn't exist to be processed then we move send our packet; 
    }   
    if(!packet_exists[1] && send_cmd[1]){
        Serial2.write(cmd_packet1, PACKET_SIZE); 
    }
    if(!packet_exists[2] && send_cmd[2]){    
        Serial3.write(cmd_packet2, PACKET_SIZE); 
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
      fee_packet_ptr[index][response_packet_counter[index]] = port->read(); 
      checksum[index] ^= fee_packet_ptr[index][response_packet_counter[index]]; 
      response_packet_counter[index]++;  
    }
  }
  
  void recieve_reply()
  {
     check_port(&Serial1, 0); 
     check_port(&Serial2, 1); 
     check_port(&Serial3, 2); 
  }
  bool set_flag(int index){
    if(check_capacity[index]){ 
      //digitalWrite(13, HIGH); 
      //response_packet_counter[index] = 0; 
      check_cap[index] = true;
    } 
  }

