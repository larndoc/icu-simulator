/*
 * Program description here
 * 
 * 
 * 
 */
 
#include <DueTimer.h>
#include <time.h>
#include <SPI.h>

#include "adc.h"
#include "communication.h"

#define SPI_PIN               41 
#define DEBUG_PIN             10
//********************************************************************************SYNC SETTINGS****************************************************************//
#define FREQUENCY             128
#define PULSE_WIDTH_US        1000
//********************************************************************************UART SETTINGS****************************************************************//
#define BAUD_RATE             115200
//******************************************************************************GLOBAL VARIABLES***************************************************************//

enum icu_modes {
  SCIENCE_MODE=0,  
  CONFIG_MODE,  
};

enum icu_modes mode  = CONFIG_MODE;
hk_packet_t hk_packet;
bool fee_enabled[3]                  = {false, false, false};
HardwareSerial* fee_ports[3]         = {&Serial1, &Serial2, &Serial3};
const uint8_t sync_pins[3]           = {11, 13, 12};

uint32_t time_counter = 0;
unsigned long t_isr;

bool cmd_packet_sent = false;
bool send_hk = false;
bool send_sci = false;
bool sending_hk = false;
bool sending_sci = false;
 
byte user_cmd = 0;
uint8_t user_fee_cmd[6] = {0};

void wait_us(unsigned long delta_us, unsigned long t) {
  while ( (micros()  - t ) < delta_us ) {
    if (micros() - t < 0) {      
      delta_us = delta_us - (0xFFFFFFFF - t);
    }
  }
}

void fee_activate(uint8_t fee) {  
  if (fee < 3) {
    if(!fee_enabled[fee]) {
      fee_ports[fee]->begin(BAUD_RATE);
      fee_enabled[fee] = true; 
    }
  }
}

void fee_deactivate(uint8_t fee) {
  if (fee < 3) {
    if(fee_enabled[fee]) {
      fee_ports[fee]->end();
      fee_enabled[fee] = false; 
    }
  }
}

void timer_isr() {
  int i;
  time_counter++;
  t_isr = micros(); 
  digitalWrite(DEBUG_PIN, HIGH);

  // create trigger flags
  if((time_counter % HK_CADENCE)==0) {
    send_hk = true;
    init_hk_packet(time_counter - 1);    
  }

  // create sync pulse rising edge
  if(mode == SCIENCE_MODE) {
    if((time_counter % SCI_CADENCE)==0) {
      send_sci = true; 
      init_sci_packet(time_counter - SCI_CADENCE);
    }
    for(i = 0; i < 3; i++){
      if(fee_enabled[i]){
        digitalWrite(sync_pins[i], HIGH);         //setting up of the pins 
      }
    }
  }

  // process old data if a packet was sent
  if(cmd_packet_sent) { 
    cmd_packet_sent = false;   
    for(i = 0; i < 3; i++){
      if(fee_enabled[i]){
        process_fee_response(i);
      }        
    }
    // emulate real ICU processing time here
    //wait_us(PULSE_WIDTH_US, t_isr); 
  }

  // init packet transfer and generate sync falling edge
  if(mode == SCIENCE_MODE) { 
    for(i = 0; i < 3; i++){
      if(fee_enabled[i]){
        send_fee_cmd(fee_ports[i], i);
      }
    }
    cmd_packet_sent = true;
    for (i = 0; i < 3; i++) {
      if (fee_enabled[i]) {
        digitalWrite(sync_pins[i], LOW);
      }
    } 
  }
  digitalWrite(DEBUG_PIN, LOW);
}


/*
   initialize the Serial monitor to print debug information
   each interface is driven by a synchronisation pin.
   only initialize the sync and communication pins if the fee_enabled flag to the respective interface is enabled
   port[i] represents each set of communication pins respectively.
*/
void setup() {
  int i;

  init_sci_data();

  for(i=0; i<3; i++) {
    pinMode(sync_pins[i], OUTPUT);
    digitalWrite(sync_pins[i], LOW);
  }
  pinMode(SPI_PIN, OUTPUT);
  pinMode(DEBUG_PIN, OUTPUT);
  Serial.begin(BAUD_RATE);
  SPI.begin(); 
  Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
}

void loop() {

  // stuff to do all the time
  // 1) check for external input from PC
  // 2) send HK data
  // 3)
   
  switch(user_cmd) {  
    case 0x03:
      mode = SCIENCE_MODE; 
      user_cmd = 0;
      break; 

    case 0x02:
      // serial input buffer should be bigger than 6
      if(Serial.available() >= 6) {
        Serial.readBytes(user_fee_cmd, 6);
        create_cmd_packet(user_fee_cmd); 
        user_cmd = 0;
      }
      //the input remains the same, if we are in science mode we stay in science mode and if we are in config mode, then we stay in config mode, hence it is not required to update the input  
      break; 
      
  case 0x04:
    mode = CONFIG_MODE;
    user_cmd = 0;
    break;

  
  case 0x05:
    if(Serial.available()) {
      if(mode == CONFIG_MODE) {
        // only in config mode activate an fee
        fee_activate(Serial.read());
      } else {
        // just read and throw away otherwise
        Serial.read();
      }
      user_cmd = 0;
    }
    break; 

  
  case 0x06: 
    if(Serial.available()) {
      if(mode == CONFIG_MODE) {
        fee_deactivate(Serial.read());   
      } else {
        // just read and throw away otherwise
        Serial.read();
      }
      user_cmd = 0;
    }
    break; 

  default:
    // if no user command was set, check for a new one
    if(Serial.available()) {
      user_cmd = Serial.read();
    }
  }


  // only HK send if Sci is not sending already
  if(send_hk && !sending_sci){
    update_hk();
    sending_hk = send_hk_packet();
    // this will reset the send_hk flag once sending is done
    send_hk = sending_hk;
  }

  // state machine of the ICU
  switch (mode) {   
    case CONFIG_MODE: 
      // nothing to do in CONFIG MODE yet     
      break; 
    case SCIENCE_MODE:
      // receive fee responses, if we sent a command
      if(cmd_packet_sent){
        for (int i = 0; i < 3; i++) {
          if(fee_enabled[i]){
            receive_fee_response(fee_ports[i], i);
          }
        }
      }
      // send Sci data, if not already sending HK data
      if(send_sci && !sending_hk) {
        sending_sci = send_sci_packet();
        // this will reset the send_sci flag once sending is done
        send_sci = sending_sci;
      }      
      break; 
  }
} // loop ends

void update_hk(){
  byte p_loc[32];
  adc_read_all(1, hk_packet.pcu); 
  adc_read_all(0, hk_packet.pcu+16);
  /*copying first channel into p_loc*/ 
  int i;
  int j;
  for( i = 0, j = 15; i < 16; i++, j--){
    p_loc[i] = hk_packet.pcu[j]; 
  }
  /*copying second channel into p_loc*/
  for( i = 16, j = 31; i < 32; i++, j--){
    p_loc[i] = hk_packet.pcu[j];
  }
  
  for(i = 0; i < 16; i++){
    hk_packet.pcu[i] = p_loc[i];
  }
  for (i= 16; i < 32; i++){
    hk_packet.pcu[i] = p_loc[i];
  }
}

