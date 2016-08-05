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

//********************************************************************************CLOCK INFORMATION****************************************************************//
#define FREQUENCY             128
#define PERIOD_US             100000/FREQUENCY
#define BAUD_RATE             115200

//*******************************************************************************ICU COMMAND PACKET INFO**********************************************************//
#define BYTE_SIZE             8
#define PACKET_SIZE           6
#define PACKETS_TO_TRANSFER   3 

//******************************************************************************FEE PACKET INFORMATION************************************************************//
#define FEE_PACKET_SIZE       100 
#define PACKETS_RECIEVED      3
#define STATUS                0

//******************************************************************************GLOBAL VARIABLES***************************************************************//

/*set of states that the user transverses through based on the input(which can be intrinsic or defined by the user(external)*/ 
enum set {
  SCIENCE_MODE=0, 
  CREATE_PC_PACKET, 
  CLEAR_PC_PACKET,
  STORE_TO_PC, 
  BEGIN_SYNC,
  CONFIG_MODE,  
  DEFAULT0
  };

enum set task  = DEFAULT0;
enum set input = DEFAULT0; 

/*fee packet and pointer to the three fee_packets, the data structure used for fee_packet is a union which is included in the folder fee_packet_structure*/ 
fee_paket fee_packet[3];
fee_paket* fee_packet_ptr[3]         = {&fee_packet[0], &fee_packet[1], &fee_packet[2]} ;

/*declaration of the pc packet, used to package the recieved bytes from the three interfaces and write it out the serial port, the struct used for pc packet is a union defined in pc_data_dump.h */
pc_data pc_packet                    = {STATUS, 0, 0, 0, 0};       
pc_data* pc_packet_ptr               = &pc_packet;
byte* pc_data[3]                  = {pc_packet_ptr->sci_fib, pc_packet_ptr->sci_fob, pc_packet_ptr->sci_fsc};
byte* pc_fee_counter[3]              = {&pc_packet_ptr->n_fib, &pc_packet_ptr-> n_fob, &pc_packet_ptr->n_fsc};

/*a 2-D (3 x 6) array for the command packets that includes the command packet to be sent to each interface */ 
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
  
    bytes1 = Serial.available(); 
    if(bytes1 > 0){
    if(bytes1 == 1){ 
    byte cmd_id = Serial.read(); 
    
    if(cmd_id == '\x03'){
      input = SCIENCE_MODE; 
    }

    else if(cmd_id == '\x02'){
           int bytesToRead = Serial.available(); 
      while(bytesToRead == 0); 
      if(bytesToRead > 0){
        uint8_t arr[bytesToRead];
        Serial.readBytes(arr, bytesToRead); 
        const byte fee_number = arr[0];
        const byte read_write = arr[1]; 
        const byte config_id =  arr[2];
        byte config_val[3];
        const byte * config_val_ptr;
        config_val_ptr = config_val;  
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
          byte checksum_for_config_val = 0; 
          byte checksum; 
          write_command_packet(fee_number, config_val_ptr, config_id);
          for(int i = 0; i < 3; i++){
             checksum_for_config_val ^= config_val[i];  
          }
         checksum = checksum_for_config_val ^ fee_number ^ read_write ^config_id;
         cmd_packet[fee_number][5] = checksum; 
        }
      }
      input = SCIENCE_MODE;
    }

    else if(cmd_id == '\x04'){
      input = CONFIG_MODE;
    }

    else if(input == CONFIG_MODE && cmd_id == '\x05'){
      while(Serial.available() == 0); 
      if(Serial.available() > 0){
        byte interface = Serial.read(); 
        fee_activate(interface);
        input = CONFIG_MODE; 
      }
      
    }
    else if(input == CONFIG_MODE && cmd_id == '\x06'){
      while(Serial.available() == 0); 
      if(Serial.available() > 0){
        uint8_t interface = Serial.read(); 
        fee_deactivate(interface);
        input = CONFIG_MODE; 
      }
    }
    }
    task = DEFAULT0;
    }
    
    
  switch (task) {   
     case CONFIG_MODE: 
      input = CONFIG_MODE; 
      task = DEFAULT0;            //disable the timer isr in config_mode i.e stop generating any sync pulses
     break; 
      
    case STORE_TO_PC:   
      Serial.write(pc_packet.arr, 8); 
      if(*pc_fee_counter[0] == 1){
        Serial.write(pc_packet.sci_fib, 10);
      }
      if(*pc_fee_counter[1] == 1){
        Serial.write(pc_packet.sci_fob, 10); 
      }
      if(*pc_fee_counter[2] == 1){
        Serial.write(pc_packet.sci_fsc, 10);
      }
      input = SCIENCE_MODE; 
      task = DEFAULT0;
     break; 
      
    case SCIENCE_MODE:
      if (sync_counter == old_counter) {
        for (int i = 0; i < 3; i++) {
          if(fee_enabled[i]){
            check_port(port[i], i);
          }
        }
        input = SCIENCE_MODE;
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
  
  
     //***********************************************************NOTHING TO READ FROM THE SERIAL PORT******************************************************//
      task = 
        input == DEFAULT0 ? DEFAULT0 : 
        input == SCIENCE_MODE ? SCIENCE_MODE : 
        input == CONFIG_MODE ? CONFIG_MODE : 
        input == CREATE_PC_PACKET ? CREATE_PC_PACKET : 
        STORE_TO_PC;  
    break ;
    
    default: ;
  }
}


void fee_activate(int index){
  
  if ( (index) > 2 || (index) < 0){
    return;  
  }
  else{
    create_interface(index);  
  }
}

void delete_interface(char index){
  
  deactivate_pins(index); 
  fee_enabled[index] = false; 
  *pc_fee_counter[index] = 0; 
}

void create_interface(int index){
  
  activate_pins(index); 
  fee_enabled[index] = true; 
  *pc_fee_counter[index] = 1;
}

void fee_deactivate(char index){
  if ((index) > 2 || (index) < 0){
    return; 
  }
  else{
    delete_interface(index);  
  }
}

void activate_pins(int index){
   pinMode(sync_pins[index],  OUTPUT); 
   digitalWrite(sync_pins[index], LOW); 
   port[index]->begin(BAUD_RATE);
}

void deactivate_pins(char index){
  pinMode(sync_pins[index], INPUT);
  digitalWrite(sync_pins[index], LOW); 
  port[index]->end(); 
}

void create_pc_packet(int index){
  /*if index == 0 then set size_of_data to FIB_SCI_DATA, if index == 1 then set size_of_data to FOB_SCI_DATA_SIZE and if index == 2 then set size_of_data to FSC_SCI_DATA_SIZE */
  
    
  if(packet_exists[index]){
     for(int i = 0; i < 10; i++){
             pc_data[index][i] = (fee_packet_ptr[index] -> science_data[i]); 
     }
      packet_exists[index] = false; 
  }
}

void write_command_packet(const uint8_t fee_interface, const uint8_t* config_val, const uint8_t config_id)
{
  
  change_command_packet[fee_interface] = true; 
  cmd_packet[fee_interface][0] = 5; 
  cmd_packet[fee_interface][1] = config_id;
  for(int i = 0; i < 3; i++){
    cmd_packet[fee_interface][i+2] = config_val[i];  
  } 
}


