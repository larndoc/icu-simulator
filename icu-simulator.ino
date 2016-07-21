#include <Time.h>
#include <TimeLib.h>

#include <DueTimer.h>
#include <time.h> 
#include "packets.h" 
#include "clock.h"
#include "errors.h"
#include "fee_packet_structure.h"
bool toggled; 
union fee_paket fee_packet1_temp; 
union fee_paket fee_packet2_temp; 
union fee_paket fee_packet3_temp; 
uint8_t cmd_packet[PACKET_SIZE]   = {1, 0, 0, 0, 0, 1};
uint8_t cmd_packet1[PACKET_SIZE]  = {1, 0, 0, 0, 0, 1}; 
uint8_t cmd_packet2[PACKET_SIZE]  = {1, 0, 0, 0, 0, 1}; 
uint16_t global_packet_counter[3] = {0, 0, 0}; 
bool checksum[3]                  = {false, false, false}; 
bool packet_exists[3]             = {false, false, false}; 
bool send_cmd[3]                  = {true, true, true};
uint8_t elapsed_time = 0; 
uint8_t fee_packet[FEE_PACKET_SIZE]; 
uint8_t fee_packet1[FEE_PACKET_SIZE]; 
uint8_t fee_packet2[FEE_PACKET_SIZE];
uint8_t* fee_packet_ptr = fee_packet; 
uint8_t* fee_packet1_ptr= fee_packet1; 
uint8_t* fee_packet2_ptr= fee_packet2; 
uint16_t init_val; 
uint16_t final_val = 0;
time_t current_time = 0; 
time_t current; 
bool overflow = false; 


bool send_command = false;

bool check_cap[3]; 

bool recieved_reply = false; 


void process_packet(){
//  check_checksum(fee_packet1, 1);           //set the flag if the checksum doesn't match
 
  //check_error(fee_packet1[0]);              //light up the LED if something is wrong. 
}

void duty_cycle(unsigned long pulse_width_us){
  t = micros();
 if(micros() - t == 0){
      elapsed_time =  elapsed_time + 76; //overflow has occured
 }

  while( (micros() + elapsed_time - t ) < pulse_width_us ){
    } 
}

void check_error(uint8_t* tst){
      if(*tst == NO_ERROR)
          Serial.println("No Error"); 
       else if(*tst == INVALID_ICU_PACKET_CHECKSUM)
          Serial.println("Invalid ICU packet checksum"); 
  
}


void timer_isr(){   
     async_set(); 
     duty_cycle(1000);
     serial_write(send_cmd); //generation of 128 Hz signals on the output pin   
     async_clear(); 
}


void setup() {  
    initialize_pins(); 
    initiate_communication(); 
    Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start(); 
}

void check_checksum(uint8_t* fee_packet_ptr, int index)
{
  if(fee_packet_ptr[FEE_PACKET_SIZE - 1] != checksum[index])
  {
    fee_packet_ptr[0] = INVALID_ICU_PACKET_CHECKSUM;
  }
  
 // check_error(fee_packet_ptr); 
}

void reset_counter(){
  response_packet_counter[0] = 0; 
  response_packet_counter[1] = 0; 
  response_packet_counter[2] = 0; 
}
  time_t old_val = 0; 
  uint8_t*old_packet;
  
void print_packet(uint8_t* test_packet, uint8_t index){
  uint16_t bit_rate = 0; 
  current_time = now(); 
  //init_val = global_packet_counter[index]; 
  final_val = global_packet_counter[index];
  bit_rate = (final_val * response_packet_counter[index]) >> 3; 
  //unsigned normalize = fast_divide(bit_rate); 
  //String Bit_rate = "bit rate: " + String(normalize);
  String time_elapsed = "time elapased in seconds: " + String(old_val) + "\t"; 
  //String fee_packet_size = "fee packet_size: " + String(response_packet_counter[index]) + " bytes \t"; 
  String interface = "recieved from interface: " + String(index + 1) + "\t"; 
  //String packets_transferred = "Total packets transferred: "  + String(final_val) ;
  Serial.print(time_elapsed); 
  //Serial.println(interface);
  //Serial.print(time_elapsed);
  //Serial.print(fee_packet_size);   
  //Serial.print("IF# ");
  Serial.print(index + 1);
  Serial.print("-");
  Serial.println(response_packet_counter[index]);
  //Serial.println(")");  
 // Serial.print(packets_transferred);
  //Serial.println(" "); 
  //Serial.println(Bit_rate); 
  global_packet_counter[index] = 0;
  old_val = current_time; 
  old_packet = test_packet; 
}


int fast_divide(uint8_t bit_rate)
{
  unsigned q, r;
  q = (bit_rate >> 1) + (bit_rate >> 2);
  q = q + (q >> 4);
  q = q + (q >> 8);
  q = q + (q >> 16);
  q = q >> 3;
  r = bit_rate - q*10;
return q + ((r + 6) >> 4);
}
void reset_fee_packet(int index)
{
  response_packet_counter[index] = 0; 
  packet_exists[index] = false; 
  checksum[index] = 0; 
}

void loop(){
   recieve_reply(); 
  /*
  if(send_command == false && packet_exists[0] == true){
     print_packet(fee_packet, 0); 
     reset_fee_packet(0); 
     packet_exists[0] = false; 
    }
   if(send_command == false && packet_exists[1] == true){
    print_packet(fee_packet1, 1); 
    reset_fee_packet(1);  
    packet_exists[1] = false; 
   }
   if(send_command == false && packet_exists[2] == true){
    print_packet(fee_packet2, 2); 
    reset_fee_packet(2);   
    packet_exists[2] = false; 
   }
   /*
  if(send_command); 
  // Serial.println(fee_packet1[4]);
  //check_checksum(fee_packet1, 1); 
  
  
  /*
   
 if(send_command == false){
     //Serial.println("A");
     recieve_reply();    
    // check_checksum(fee_packet1, 1);
    // check_error(fee_packet[0]); 
     //check_error(fee_packet1[0]); 
    // check_error(f1->rep_packet[2]); 
  }
   if(!send_command && recieved_reply == true){
      //check_checksum(fee_packet, 0);
     check_checksum(fee_packet1, 1); 
     // check_checksum(fee_packet2, 2);  
  }
  */
}




