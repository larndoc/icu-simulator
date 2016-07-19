#include <DueTimer.h>
#include "packets.h" 
#include "clock.h"
#include "errors.h"
bool toggled; 
bool prev = true;  
uint8_t cmd_packet[PACKET_SIZE]   = {0, 5, 0, 0, 0, 1};
uint8_t cmd_packet1[PACKET_SIZE]  = {1, 1, 1, 1, 0, 0}; 
uint8_t cmd_packet2[PACKET_SIZE]  = {0, 8, 7, 12, 11, 123}; 
bool packet_exists[3]             = {false, false, false}; 
bool send_cmd[3]                  = {true, true, false};

uint8_t fee_packet[FEE_PACKET_SIZE]; 
uint8_t fee_packet1[FEE_PACKET_SIZE]; 
uint8_t fee_packet2[FEE_PACKET_SIZE];
uint8_t* fee_packet_ptr = fee_packet; 
uint8_t* fee_packet1_ptr= fee_packet1; 
uint8_t* fee_packet2_ptr= fee_packet2; 
 
bool checksum[3] = {0, 0, 0}; 
 


bool send_command = false;

bool check_cap[3]; 

bool recieved_reply = false; 


void process_packet(){
//  check_checksum(fee_packet1, 1);           //set the flag if the checksum doesn't match
 
  //check_error(fee_packet1[0]);              //light up the LED if something is wrong. 
}
void duty_cycle(unsigned long pulse_width_us){
  t = micros();
  //unsigned long temp = pulse_width_us;
 
 // overflow(); 
  // fix overflow issue
  //delay(pulse_width_us - micros())
  //digitalWrite(13, LOW); 
 // t = micros();
  while( ( micros() - t ) < pulse_width_us ){
    } 
    //digitalWrite(13, LOW);
  //old_time = t;  
  // while loop waits until pulse_width_us time is over
}

void check_error(uint8_t tst){
      switch(tst){
       case NO_ERROR:
          Serial.println("No Error"); 
          break; 
       case INVALID_ICU_PACKET_CHECKSUM:
          Serial.println("Invalid ICU packet checksum"); 
          break; 
       default: ;
      }
  
}


void timer_isr(){   
     async_set(); 
     duty_cycle(1000);
    send_command = true;
    serial_write(send_cmd); //generation of 128 Hz signals on the output pin   
    //check_checksum(fee_packet1, 1);
    send_command = false; 
    async_clear(); 
    //digitalWrite(13, LOW);
}


void setup() {  
    initialize_pins(); 
    initiate_communication(); 
    Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start(); 
}

void check_checksum(int fee_packet[FEE_PACKET_SIZE], int index)
{
  if(fee_packet1[FEE_PACKET_SIZE - 1] != checksum[index])
  {
    fee_packet1[0] = INVALID_ICU_PACKET_CHECKSUM;
  }
  Serial.println(response_packet_counter[1]); 
 
  check_error(fee_packet1[0]); 
}

void reset_counter(){
  response_packet_counter[0] = 0; 
  response_packet_counter[1] = 0; 
  response_packet_counter[2] = 0; 
}

void print_packet(uint8_t* test_packet, int index){
  //for (int i = 0; i < response_packet_counter[index]; i++){
   // int temp  = (fee_packet[response_packet_counter[index]]);
   // Serial.println(temp);
 // }
  Serial.print("FEE PACKET SIZE:"); 
  Serial.print(" "); 
  Serial.println(response_packet_counter[1]); 
}

void reset_fee_packet(int index)
{
  response_packet_counter[index] = 0; 
  packet_exists[index] = false; 
  checksum[index] = 0; 
}

void loop(){
  while( send_command == false){
   // Serial.println("A"); 
   recieve_reply(); 
  }
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




void read_reply()
{
//  display_error();
 // validate_checksum(); 
}


/*
  void validate_checksum(){
    int result = 0; 
    for (int i = 0; i < 64; i++){
      result = result | data[i];
    }
    if (result != data[size_of_FEE_byte]){
      Serial.println("CHECKSUM does not match"); 
    }
  }
*/




