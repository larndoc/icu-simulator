  #include "test.h"
  #include "packets.h" 
  #define PACKET1    (i1->packets[0]) 
  #define PACKET2    (i1->packets[1])
  #define PACKET3    (i1->packets[2])
  #define FEE_PACKET1 (f1->rep_packet[0])
  #define FEE_PACKET2 (f1->rep_packet[1])
  #define FEE_PACKET3 (f1->rep_packet[2]) 
  bool packet_found_1 = false;  
  bool packet_found_2 = false;  
  bool packet_found_3  = false; 
  void initiate_communication(){
      Serial.begin(9600); 
      Serial1.begin(BAUD_RATE); 
      Serial2.begin(BAUD_RATE); 
      Serial3.begin(BAUD_RATE); 
  }
  
  void serial_write(bool send_cmd[3]){  
    if(send_cmd[0]){ 
        Serial1.write(cmd_packet, PACKET_SIZE); 
    }   
    if(send_cmd[1]){
        Serial2.write(cmd_packet1, PACKET_SIZE); 
    }
    if(send_cmd[2]){    
        Serial3.write(cmd_packet2, PACKET_SIZE); 
    }
  }
  
  
  void load_packets(uint8_t cmd_packets[PACKET_SIZE], uint8_t data[PACKET_SIZE])
  {
    for(int i = 0; i < PACKET_SIZE; i++){
      cmd_packets[i] = data[i]; 
    }
  }
  
  
  void check_pckt_size(packet* p1)
  {
    if( sizeof(p1)/sizeof((p1)[0]) !=  PACKET_SIZE){
      Serial.println(" the size of the array doesn't meet the specification"); 
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
  
  
  void recieve_reply()
  {
  //Serial.println("A");
    if(!send_command){
      Serial.println("A");
        if(Serial1.available()){
          Serial.println("B");
          packet_found_1 = true;
                   if (check_capacity(response_packet_counter[0])){
                          response_packet_counter[0] = 0; 
                          check_cap[0] = true; 
                   }
                   fee_packet[response_packet_counter[0]] = Serial1.read(); 
                   checksum[0] ^= fee_packet[response_packet_counter[0]]; // Serial.println(FEE_PACKET1.bytes[response_packet_counter[0]]); 
                   response_packet_counter[0]++;
         }
  
         if(Serial2.available()){
          packet_found_2 = true; 
                   if(check_capacity(response_packet_counter[1])){
                           check_cap[1] = true; 
                   } 
                   fee_packet1[response_packet_counter[1]] = Serial2.read(); 
                   checksum[1] ^= fee_packet1[response_packet_counter[1]];  
                   response_packet_counter[1]++;  
                   //if(response_packet_counter[1] == 6){
                    //  packet_exists = true; 
                     // response_packet_counter[1] = 0; 
                   //}
         }
         
         if(Serial3.available()){
          packet_found_3 = true; 
                     if (check_capacity(response_packet_counter[2])){
                          check_cap[2] = true; 
                     }
             
                     fee_packet2[response_packet_counter[2]] = Serial3.read();
                     checksum[2] ^= fee_packet[response_packet_counter[2]];  
                     //Serial.println(FEE_PACKET3.bytes[response_packet_counter[2]]);  
                     response_packet_counter[2]++; 
                     //if(response_packet_counter[2] == 6){
                      //  response_packet_counter[2] = 0; 
                     //}
                    
         }

         if(!Serial1.available() && packet_found_1 == true){
          packet_exists[0] = true; 
          packet_found_1 = false; 
         }
         if(!Serial2.available() && packet_found_2 == true){
          packet_exists[1] = true; 
          packet_found_2 = false; 
         }
         if(!Serial3.available() && packet_found_3 == true){
          packet_exists[2] = true; 
          packet_found_3 = false; 
         }
   
         
    }
    
  }

