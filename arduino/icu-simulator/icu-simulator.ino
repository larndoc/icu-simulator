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
  CONFIG_MODE,  
  };

enum set task  = CONFIG_MODE;
/*fee packet and pointer to the three fee_packets, the data structure used for fee_packet is a union which is included in the folder fee_packet_structure*/ 
int total_count = 0;
fee_paket fee_packet[3];
fee_paket* fee_packet_ptr[3]         = {&fee_packet[0], &fee_packet[1], &fee_packet[2]} ;
byte pc_packet_arr[100] ;
/*declaration of the pc packet, used to package the recieved bytes from the three interfaces and write it out the serial port, the struct used for pc packet is a union defined in pc_data_dump.h */
pc_data pc_packet                    = {STATUS, 0, 0, 0, 0};       
pc_data* pc_packet_ptr               = &pc_packet;
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
const uint8_t led_pin    = 10;
const uint8_t old_counter = 1; 
unsigned long current_time;
unsigned long t;
bool overflow = false;
unsigned sync_counter                = 0;
bool change_command_packet          = false;
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
    sync_counter++; 
      if(task == SCIENCE_MODE) {
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
  
          wait(time_us); 
   
     
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

  /****************************************************************************************************************EXTERNAL INPUTS THAT CHANGE THE CURRENT STATE WITHIN THE STATE DIAGRAM************************************************************************************/
    if(Serial.available() > 0){   
         byte cmd_id = Serial.read();
         byte deactive_selector; 
         byte active_selector; 
         switch(cmd_id){
         
         case 0x03:
          task = SCIENCE_MODE; 
          break; 

          case 0x02:
          {
          int counter = 0; 
          uint8_t fee_command[6]; 
          //counter is the number of bytes that were read from the stream into a buffer
          //fee_command is the buffer in this case
          counter = Serial.readBytes(fee_command, 6); 
          if (counter != 6){ 
            // we were not able to read 6 bytes into the buffer, catching appropiate error
          }
          else{
            int fee_number = fee_command[0];
            int read_write = fee_command[1]; 
            int config_id =  fee_command[2];
            byte checksum = 0;
            byte config_val[3];
            byte * config_val_ptr;
            config_val_ptr = config_val;  
            for (int i = 0; i < 3; i++){
              config_val_ptr[i] =  fee_command[2 + i]; 
          }
          cmd_packet[fee_number][0] = read_write == 0 ? 3 : 5;
           for(int i = 0; i < 5; i++)
           {
              checksum ^= cmd_packet[fee_number][i];  
           }
            cmd_packet[fee_number][5] = checksum; 
            change_command_packet = true;                 //indicates that the upgrade was complete
            write_command_packet(fee_number, config_val_ptr, config_id);              //update the config command value in the icu packet
            cmd_packet[fee_number][5] = checksum; 
            change_command_packet = true; 
          }
          }
           //the input remains the same, if we are in science mode we stay in science mode and if we are in config mode, then we stay in config mode, hence it is not required to update the input  
           break; 

          case 0x04:
            task = CONFIG_MODE;
            break;

          case 0x05:
              while(Serial.available() == 0);
              if(task == CONFIG_MODE){  
                active_selector = Serial.read(); 
                fee_activate(active_selector);
              }
             break; 
          
          case 0x06: 
              while(Serial.available() == 0); 
              if(task == CONFIG_MODE){
               deactive_selector = Serial.read(); 
               fee_deactivate(deactive_selector); 
             }
         break; 
         
         default:;
    }
    }
    
  switch (task) {   
    
 /****************************************************************************************************************************CONFIGURATION MODE***********************************************************************************************************************/
     
     case CONFIG_MODE: 
      task = CONFIG_MODE;            //disable the timer isr in config_mode i.e stop generating any sync pulses
     break; 

/*****************************************************************************************************************************SCIENCE MODE*****************************************************************************************************************************/
    case SCIENCE_MODE:
    if(sync_counter == old_counter){
        for (int i = 0; i < 3; i++) {
          if(fee_enabled[i]){
            check_port(port[i], i);
          }
        }
    }
            /**it would probably make sense to have too variables, sync_counter and old_counter, initially both sync_counter and old_counter are set to zero, but at the end of every timer isr, we would increment sync_counter and therefore sync_counter > old_counter, this acts as an indication that we have hit a new sync pulse and therefore we must transmit the packet to pc  
             * otherwise if sync_counter == old_counter, means we havent gone into the timer isr again and we need to listen for any incoming data.. 
             * 
             */
            else if(sync_counter > old_counter){
              old_counter = sync_counter; 
              if(packet_exists[0] == true  || packet_exists[1] == true|| packet_exists[2] == true){
                bool packet[3] = {packet_exists[0], packet_exists[1], packet_exists[2]};  
                
                 /****preparing the header, first 8 bytes of pc_packet_arr should be the header that is defined globally****/
                 for(int i = 0; i < 8; i++){
                  pc_packet_arr[i] = pc_packet.arr[i]; 
                }

                /***updating total count to 8 as 8 bytes have been read************************/ 
                total_count =  8;
              
              
              
              if(pc_packet.n_fib == 1 && (packet[0] == true)){
                for(int j = 0; j < 10; j++){
                  pc_packet_arr[j + total_count] = fee_packet_ptr[0]->science_data[j];
                }
                packet_exists[0]  = false; 
                total_count = total_count + 10; 
              }
              
              
              if(pc_packet.n_fob == 1 && (packet[1] == true)){
                for(int j= 0; j < 10; j++){
                  pc_packet_arr[j + total_count] = fee_packet_ptr[1]->science_data[j];
                }
                packet_exists[1] = false; 
                total_count = total_count + 10; 
              }
              if(pc_packet.n_fsc == 1 && (packet[2]== true)){
                for(int j = 0; j < 10; j++){
                  pc_packet_arr[j + total_count] = fee_packet_ptr[2] -> science_data[j] ;
              }
              packet_exists[2] = false; 
              total_count = total_count + 10; 
              }
         
            }
              
          /**if total_count is 0 you are not going to write any bytes***/ 
          Serial.write(pc_packet_arr, total_count);
          total_count = 0; 
         }
        
        task = SCIENCE_MODE; /***could probably get rid of this, but left it here due to improved readibility***/  
     break; 

/******************************************************************************************************************************PC_TRANSMIT*********************************************************************************************************************************/
    
    default:
      task = CONFIG_MODE;
  }
}

void fee_activate(int index){
  
  if ( (index) > 2 || (index) < 0){
    return;  
  }
  else{
      activate_pins(index); 
  fee_enabled[index] = true; 
  *pc_fee_counter[index] = 1; 
  }
}


void fee_deactivate(char index){
  if ((index) > 2 || (index) < 0){
    return; 
  }
  else{
    deactivate_pins(index); 
  fee_enabled[index] = false; 
  *pc_fee_counter[index] = 0; 
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

int update_pc_packet(){
  /*if index == 0 then set size_of_data to FIB_SCI_DATA, if index == 1 then set size_of_data to FOB_SCI_DATA_SIZE and if index == 2 then set size_of_data to FSC_SCI_DATA_SIZE */
int bytesToSend = 0; 
for(int i = 0; i < 3; i++){    
  if(packet_exists[i]){
     bytesToSend = bytesToSend + 10; 
  }
}
return bytesToSend; 
}

void write_command_packet(int fee_interface, const uint8_t* config_val, int config_id)
{
  cmd_packet[fee_interface][1] = config_id;
  for(int i = 0; i < 3; i++){
    cmd_packet[fee_interface][i+2] = config_val[i];  
  } 
}




