#include <Time.h>
#include <TimeLib.h>
#include <DueTimer.h>
#include <time.h> 
#include "clock.h"
#include "errors.h"
#include "fee_packet_structure.h"
#include "packets.h"
#include "pc_data_dump.h"
#define SCIENCE_DATA 1 

enum st {ADD_DATA, SEND, STORE_TO_PC} task; 
fee_paket fee_packet[3];  
fee_paket* fee_packet_ptr[3]         = {&fee_packet[0], &fee_packet[1], &fee_packet[2]} ;
pc_data pc_packet                    = {SCIENCE_DATA, 0, N_FIB, N_FOB, N_FSC, NULL, NULL, NULL};
pc_data* pc_packet_ptr               = &pc_packet;
byte* pc_data[3]                     = {pc_packet_ptr->sci_fib, pc_packet_ptr->sci_fob, pc_packet_ptr->sci_fsc};                      
uint8_t cmd_packet[PACKET_SIZE]      = {1, 0, 0, 0, 0, 1};
uint8_t cmd_packet1[PACKET_SIZE]     = {1, 0, 0, 0, 0, 1}; 
uint8_t cmd_packet2[PACKET_SIZE]     = {1, 0, 0, 0, 0, 1}; 
uint16_t global_packet_counter[3]    = {0, 0, 0}; 
uint8_t response_packet_counter[3]   = {0, 0, 0};
bool checksum[3]                     = {false, false, false}; 
bool packet_exists[3]                = {false, false, false}; 
bool fee_enabled[3]                  = {true, true, true};
HardwareSerial* port[3]              = {&Serial1, &Serial2, &Serial3};
const uint8_t sync_pins[3]           = {11, 12, 13}; 
const uint8_t led_pin                = 10; 
unsigned long current_time; 
unsigned long t;  
bool overflow = false; 
unsigned long sync_counter           = 0;
unsigned long old_counter = 0;  
bool send_command = false;

bool check_cap[3]; 

bool recieved_reply = false; 


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
    sync_counter++;
    unsigned long time_us = 1000; 
    for(int i = 0; i < 3; i++){
      if(fee_enabled[i]){
        digitalWrite(sync_pins[i], HIGH);
        pc_data[i] = fee_packet_ptr[i]->science_data;        
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
  pinMode(led_pin, OUTPUT); 
  Serial.begin(250000); 
  while(Serial.available()==0){
  }
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


/*
 * void print_packet is used to print debug information
 */
  
void print_packet(union fee_paket* test_packet, uint8_t index){
  digitalWrite(10, HIGH); 
  current_time = now(); 
  String time_elapsed = "time elapased in s: " + String(current_time) + "\t"; 
  String interface = "recieved from interface: " + String(index + 1) + "\t"; 
 //Serial.println(pc_packet_ptr->time1); 
  
  

 // if(fee_enabled[2]){
  //  Serial.write(pc_packet_ptr->time1); 
  //}
 
  digitalWrite(10, LOW); 
}

/*
 * implementation of a finite state machine 
 * state is represented by the variable task 
 * currently there are two states given by store_to_pc and add_data 
 * in state 1, 'store_to_pc', we know that we have data ready and package it into a form that will be understood by the PC 
 * in state 2, if sync_counter is equal to old_counter, then we stay in the same state and listen for data at all the three pins respectively otherwise we go back to state 1. 
 */ 
void loop(){
   switch(task){
    case STORE_TO_PC:
       Serial.println(pc_packet_ptr->time1); 
    
        task = ADD_DATA; 
    case ADD_DATA: 
      if(sync_counter == old_counter){
        for(int i = 0; i < 3; i++){
          check_port(port[i], i);  
        }
        task = ADD_DATA;
      }
      else if(sync_counter > old_counter){                      
        old_counter = sync_counter; 
        task = STORE_TO_PC;
      }
      
      default: ; 
   }
    //Serial.write(fee_packet_ptr[0]->science_data, 10); 

}



