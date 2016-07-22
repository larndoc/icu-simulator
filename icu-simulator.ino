#include <Time.h>
#include <TimeLib.h>

#include <DueTimer.h>
#include <time.h> 
#include "packets.h" 
#include "clock.h"
#include "errors.h"
#include "fee_packet_structure.h"
union  fee_paket fee_packet[3];  
union  fee_paket* fee_packet_ptr[3]  = {&fee_packet[0], &fee_packet[1], &fee_packet[2]} ;
uint8_t cmd_packet[PACKET_SIZE]      = {1, 0, 0, 0, 0, 1};
uint8_t cmd_packet1[PACKET_SIZE]     = {1, 0, 0, 0, 0, 1}; 
uint8_t cmd_packet2[PACKET_SIZE]     = {1, 0, 0, 0, 0, 1}; 
uint16_t global_packet_counter[3]    = {0, 0, 0}; 
bool checksum[3]                     = {false, false, false}; 
bool packet_exists[3]                = {false, false, false}; 
bool fee_enabled[3]                  = {true, true, true};
HardwareSerial* port[3]              = {&Serial1, &Serial2, &Serial3};
const uint8_t sync_pins[3]           = {11, 12, 13}; 
unsigned long current_time; 
unsigned long t;  
bool overflow = false; 


bool send_command = false;

bool check_cap[3]; 

bool recieved_reply = false; 

void check_error(uint8_t* tst){
      if(*tst == NO_ERROR)
          Serial.println("No Error"); 
       else if(*tst == INVALID_ICU_PACKET_CHECKSUM)
          Serial.println("Invalid ICU packet checksum"); 
  
}

/*
 * void wait deals with the waiting for the desired amount of time before we start to process packets and trasmit packets to the rest of the three interfaces
 */

void wait(unsigned long delta_us){
  while( (micros()  - t ) < delta_us ){
    if(micros() - t < 0){        //indicates that a overflow has occured 
    //the time t is declared as a global variable which means that it is eight bytes.
    //if micros() < t, then we can deduce that 0xFFFFFFFF - t time has already elapsed since overflow, so now we need to wait for the amount of time given by delta_us - (0xFFFFFFFF - t); 
    delta_us = delta_us - (0xFFFFFFFF - t);      
    
    }
  } 
}



/*
 * Timer interrupt service routine that occurs after every 1/128s
 * for each of the communication pins we check to see if the flag has been set 
 * if the flag has been set, we will write HIGH at the paticular synchronisation pin
 * the wait function will stall for the amount of time defined by the variable time_us(in microseconds) before we proces the previous packet and send the next packet to the interface
 */
void timer_isr(){   
    t = micros(); 
    unsigned long time_us = 1000; 
    for(int i = 0; i < 3; i++){
      if(fee_enabled[i]){
        digitalWrite(sync_pins[i], HIGH);  
        wait(time_us);
        process_packet(fee_packet_ptr[i], i); 
        send_packet(port[i], i); 
        digitalWrite(sync_pins[i], LOW); 
    } 
}
}



/*
 * initialize the Serial monitor to print debug information 
 * each interface is driven by a synchronisation pin.
 * only initialize the sync and communication pins if the fee_enabled flag to the respective interface is enabled
 * port[i] represents each set of communication pins respectively. 
 */
void setup() { 
  Serial.begin(250000); 
  for(int i = 0; i < 3; i++){  
    if(fee_enabled[i]){
        pinMode(sync_pins[i], OUTPUT); 
        digitalWrite(sync_pins[i], LOW); 
        port[i]->begin(BAUD_RATE); 
    }
    
  }
    Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
}

void check_checksum(union fee_paket* fee_packet_ptr, int index)
{
  if(fee_packet_ptr->arr[FEE_PACKET_SIZE - 1] != checksum[index])
  {
    fee_packet_ptr[index].arr[0] = INVALID_ICU_PACKET_CHECKSUM;
  }
  
 // check_error(fee_packet_ptr); 
}

void reset_counter(){
  response_packet_counter[0] = 0; 
  response_packet_counter[1] = 0; 
  response_packet_counter[2] = 0; 
}
  
void print_packet(union fee_paket* test_packet, uint8_t index){
  digitalWrite(10, HIGH); 
  current_time = now(); 
 // unsigned normalize = fast_divide(bit_rate); 
  String time_elapsed = "time elapased in s: " + String(current_time) + "\t"; 
  String interface = "recieved from interface: " + String(index + 1) + "\t"; 
  Serial.print(time_elapsed); 
  //Serial.println(interface);
  //Serial.print(time_elapsed);
  //Serial.print(fee_packet_size);   
  //Serial.print("IF# ");
  Serial.print(index + 1);
  Serial.print("-");
  Serial.print(response_packet_counter[index]);
  Serial.println("-");
  //Serial.println(normalize);
  //Serial.println(")");  
 // Serial.print(packets_transferred);
  //Serial.println(" "); 
  //Serial.println(Bit_rate); 
  global_packet_counter[index] = 0;
  digitalWrite(10, LOW); 
}


void reset_fee_packet(int index)
{
  response_packet_counter[index] = 0; 
  packet_exists[index] = false; 
  checksum[index] = 0; 
}

void loop(){
   recieve_reply(); 
}




