/* in order to reject any noise interference the appropiate boolean values for the variable fee_enabled need to be set */ 
/*currently serial1 is configured to the synchronisation pin at pin 11, serial2 is configured to the synchronisation pin at pin 13 and serial is configured to the synchromnisation pin at pin 12 */ 
/*currently use keypad button 'A' to initiate simulation */

#include <Time.h>
#include <TimeLib.h>
#include <DueTimer.h>
#include <time.h>
#include <stdlib.h>
#include "errors.h"
#include "fee_packet_structure.h"
#include "pc_data_dump.h"
#define SCIENCE_DATA 0x0

/*clock information*/
#define FREQUENCY             128
#define PERIOD_US             100000/FREQUENCY

/*UART and FEE packet information*/
#define BYTE_SIZE             8
#define PACKET_SIZE           6
#define PACKETS_TO_TRANSFER   3 
#define BAUD_RATE             115200 
#define FEE_PACKET_SIZE       100 
#define PACKETS_RECIEVED      3

enum set {
  ADD_DATA =0, 
  SEND,
  CREATE_PC_PACKET, 
  CLEAR_PC_PACKET,
  STORE_TO_PC, 
  BEGIN_SYNC,
  SCIENCE_MODE, 
  CONFIG_MODE, 
  CONFIG_COMMAND, 
  DONE_SYNC,
  DEFAULT0
  };

enum set task  = DEFAULT0;
enum set input = DEFAULT0; 
fee_paket fee_packet[3];
fee_paket* fee_packet_ptr[3]         = {&fee_packet[0], &fee_packet[1], &fee_packet[2]} ;
pc_data pc_packet                    = {SCIENCE_DATA, 0, 0, 0, 1};        
pc_data* pc_packet_ptr               = &pc_packet;
byte* pc_data[3]                     = {pc_packet_ptr->sci_fib, pc_packet_ptr->sci_fob, pc_packet_ptr->sci_fsc};
uint8_t cmd_packet[3][PACKET_SIZE]   = {{1, 0, 0, 0, 0, 1}, {1, 0, 0, 0, 0,  1}, {1, 0, 0, 0, 0, 1}};
uint16_t global_packet_counter[3]    = {0, 0, 0};
byte interface_counter[3]            = {0, 0, 0}; 
uint8_t response_packet_counter[3]   = {0, 0, 0};
bool checksum[3]                     = {false, false, false};
bool packet_exists[3]                = {false, false, false};
bool fee_enabled[3]                  = {false, false, false};
HardwareSerial* port[3]              = {&Serial1, &Serial2, &Serial3};
const uint8_t sync_pins[3]           = {11, 13, 12};
int bytes1; 
const uint8_t led_pin                = 10;
unsigned long current_time;
unsigned long t;
bool overflow = false;
unsigned sync_counter           = 0;
unsigned long old_counter = 0;
bool change_command_packet[3]     = {false, false, false};
bool send_command = false;
bool serial_port1 = false;
bool check_cap[3];
bool recieved_reply = false;
/*prototype of the functions implemented in the filed /* 
 * void wait(unsigned long delta_us)  //when the sync pins are set high, this function is used to wait the time given by delta_us in microseconds before setting them to zero again 
 * void timer_isr()                   //called at 7.8125 ms 
 * void setup()                       //used to initialize the pins and setup the communication 
 * void print_packet()                //used to print debug information 
 * void loop()                        //used to implement the state machine 
 */

/*
   void wait deals with the waiting for the desired amount of time before we start to process packets and trasmit packets to the rest of the three interfaces
*/

void wait(unsigned long delta_us) {
  while ( (micros()  - t ) < delta_us ) {
    if (micros() - t < 0) {      //indicates that a overflow has occured
      //the time t is declared as a global variable which means that it is eight bytes.
      //if micros() < t, then we can deduce that 0xFFFFFFFF - t time has already elapsed since overflow, so now we need to wait for the amount of time given by delta_us - (0xFFFFFFFF - t);
      delta_us = delta_us - (0xFFFFFFFF - t);

    }
  }
}



/*
   Timer interrupt service routine that occurs after every 1/128s
   for each of the communication pins we check to see if the flag has been set
   if the flag has been set, we will write HIGH at the paticular synchronisation pin
   the wait function will stall for the amount of time defined by the variable time_us(in microseconds) before we proces the previous packet and send the next packet to the interface
*/
void timer_isr() {
  if(input == DEFAULT0 || input == CONFIG_MODE){
    sync_counter = 0; 
  }
            //if the current state is config_mode or default0 then we want to stop generating any sync signals 
  else {
    t = micros();
    unsigned long time_us = 1000;
    
    for(int i = 0; i < 3; i++){
      if(fee_enabled[i]){
        digitalWrite(sync_pins[i], HIGH);         //setting up of the pins 
      }
    }

    for(int i = 0; i < 3; i++){
      if(fee_enabled[i]){
        process_packet(fee_packet_ptr[i], i); 
      }
    }

     for(int i = 0; i < 3; i++) {
      if(fee_enabled[i]){
        wait(time_us); 
      }
    }
        for(int i = 0; i < 3; i++){
      if(fee_enabled[i]){
        send_packet(port[i], i);
      }
    }


   
    
    for (int i = 0; i < 3; i++) {
      if (fee_enabled[i]) {
        digitalWrite(sync_pins[i], LOW);
      }
    }
    sync_counter++; 
    pc_packet.time1 = uint32_t (__builtin_bswap32(sync_counter));
}

}



/*
   initialize the Serial monitor to print debug information
   each interface is driven by a synchronisation pin.
   only initialize the sync and communication pins if the fee_enabled flag to the respective interface is enabled
   port[i] represents each set of communication pins respectively.
*/
void setup() {
  pinMode(led_pin, OUTPUT);
  Serial.begin(BAUD_RATE);
  for (int i = 0; i < 3; i++) {
    if (fee_enabled[i]) {
      pinMode(sync_pins[i], OUTPUT);
      digitalWrite(sync_pins[i], LOW);
      port[i]->begin(BAUD_RATE);
    }

  }
  Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
}

void check_checksum(union fee_paket* fee_packet_ptr, int index)
{
  if (fee_packet_ptr->arr[FEE_PACKET_SIZE - 1] != checksum[index])
  {
    fee_packet_ptr[index].arr[0] = INVALID_ICU_PACKET_CHECKSUM;
  }

}


/*
   void print_packet is used to print debug information
*/

void print_packet(union fee_paket* test_packet, uint8_t index) {
  digitalWrite(10, HIGH);
  current_time = now();
  String time_elapsed = "time elapased in s: " + String(current_time) + "\t";
  String interface = "recieved from interface: " + String(index + 1) + "\t";
  digitalWrite(10, LOW);
}

/*
   implementation of a finite state machine
   state is represented by the variable task and we have a input variable that determines which state to go to from the default state 
*/

void loop() {
  switch (task) {
    case SCIENCE_MODE: 
        input = ADD_DATA;                                                          
    break; 
     
     case CONFIG_MODE: 
      input = CONFIG_MODE;                                                              //disable the timer isr in config_mode i.e stop generating any sync pulses
     break; 
      
    case STORE_TO_PC:   
      Serial.write(pc_packet.arr , TOTAL_PC_PCKT_SIZE);
      input = ADD_DATA; 
      task = DEFAULT0;
     break; 
      
    case ADD_DATA:
      if (sync_counter == old_counter) {
        for (int i = 0; i < 3; i++) {
          if(fee_enabled[i]){
            check_port(port[i], i);
          }
        }
        input = ADD_DATA;
      }
      else if (sync_counter > old_counter) {
        old_counter = sync_counter;
        input = CREATE_PC_PACKET;
      }
      task = DEFAULT0; 
     break; 

      case CREATE_PC_PACKET: 
        create_pc_packet(0); 
        create_pc_packet(1); 
        create_pc_packet(2); 
        input = STORE_TO_PC; 
        task = DEFAULT0; 
     
    break; 
 
  case DEFAULT0:

    bytes1 = Serial.available(); 
    if(bytes1 > 0){
    if(bytes1 == 1){ 
    int cmd_id = Serial.read(); 
    
    if(cmd_id == '3'){
      input = SCIENCE_MODE; 
    }

    else if(cmd_id == '2'){
      input = CONFIG_COMMAND; 
    }

    else if(cmd_id == '4'){
      input = CONFIG_MODE;
    }

    else if(input == CONFIG_MODE && cmd_id == '5'){
      while(Serial.available() == 0); 
      if(Serial.available() > 0){
        uint8_t interface = Serial.read(); 
        fee_activate(interface); 
        input = CONFIG_MODE; 
      }
      
    }
    else if(input == CONFIG_MODE && cmd_id == '6'){
      while(Serial.available() == 0); 
      if(Serial.available() > 0){
        uint8_t interface = Serial.read(); 
        fee_deactivate(interface); 
        input = CONFIG_MODE; 
      }
    }

    else if(input == CONFIG_COMMAND){
      int bytesToRead = Serial.available(); 
      while(bytesToRead == 0); 
      if(bytesToRead > 0){
        uint8_t arr[bytesToRead];
        Serial.readBytes(arr, bytesToRead); 
        const uint8_t fee_number = arr[0] - 48;
        const uint8_t read_write = arr[1] - 48; 
        const uint8_t config_id =  arr[2] - 48;
        uint8_t config_val[3]; 
        for (int i = 0; i < bytesToRead - 3; i++){
          config_val[i] =  arr[2 + i]; 
        }
        if(read_write == 0){
          //we want to read 
          //the rest of the code should go here 
          check_port(port[fee_number], fee_number); 
        }
        else if(read_write == 1){
          //we want to write 
          //the rest of the code should go here
          
          if(fee_number == 0){
            change_command_packet[0] = true; 
            cmd_packet[0][0] = 5; 
            cmd_packet[0][1] = config_id;
            for(int i = 0; i < 3; i++){
               cmd_packet[0][i+2] = config_val[i];  
            }
          }
          if(fee_number == 1){
            change_command_packet[1] = true;
            cmd_packet[1][1] = config_id; 
            for(int i = 0; i < 3; i++){
              cmd_packet[1][i+2] = config_val[i];
            }
          }
          if(fee_number == 2){
            change_command_packet[2] = true; 
            cmd_packet[2][2] = config_id; 
            for(int i = 0; i <  3; i++){
              cmd_packet[2][i+2] = config_val[i]; 
            }
          }
        }
      }
    }
    task = DEFAULT0;
    }
    }
  
  
     //***********************************************************NOTHING TO READ FROM THE SERIAL PORT******************************************************//
     else{
       if(input == DEFAULT0){
        task = DEFAULT0; 
        input = DEFAULT0; 
       }
       else if (input == SCIENCE_MODE){
        task = SCIENCE_MODE; 
       }
       else if(input == CONFIG_MODE){
        task = CONFIG_MODE; 
       }
       else if(input == CONFIG_COMMAND){
        task = CONFIG_COMMAND; 
       }
       else if(input == ADD_DATA){
        task = ADD_DATA; 
       }
       else if(input == CREATE_PC_PACKET){
        task = CREATE_PC_PACKET; 
       }
       else if(input == STORE_TO_PC){
        task = STORE_TO_PC; 
       }     
     }
    break ;
    
    default: ;
  }
}


void fee_activate(char index){
  if ( (index - 48) > 2 || (index - 48) < 0){
    return;  
  }
  else{
    fee_enabled[index - 48] = true; 
    activate_pins(index); 
  }
}

void fee_deactivate(char index){
  if ((index - 48) > 2 || (index - 48) < 0){
    return; 
  }
  else{
    fee_enabled[index - 48] = false; 
  }
}

void activate_pins(char index){
   pinMode(sync_pins[index - 48],  OUTPUT); 
   digitalWrite(sync_pins[index - 48], LOW); 
   port[index - 48]->begin(BAUD_RATE);
}

void deactivate_pins(char index){
  pinMode(sync_pins[index - 48], INPUT);
  digitalWrite(sync_pins[index - 48], LOW); 
  port[index - 48]->end(); 
}

void create_pc_packet(int index){
  /*if index == 0 then set size_of_data to FIB_SCI_DATA, if index == 1 then set size_of_data to FOB_SCI_DATA_SIZE and if index == 2 then set size_of_data to FSC_SCI_DATA_SIZE */
  
  int size_of_data = 
    index == 0 ? FIB_SCI_DATA_SIZE :
    index == 1 ? FOB_SCI_DATA_SIZE : 
    FSC_SCI_DATA_SIZE;  
    
  if(packet_exists[index]){
     for(int i = 0; i < size_of_data; i++){
             pc_data[index][i] = (fee_packet_ptr[index] -> science_data[i]); 
     }
      packet_exists[index] = false; 
  }
}


