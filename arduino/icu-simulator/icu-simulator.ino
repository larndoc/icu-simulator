/*
 * Program description here
 * 
 * 
 * 
 */

#include "icu-simulator-pins.h"
 
#include <DueTimer.h>
#include <time.h>
#include <SPI.h>

#include "adc.h"
#include "communication.h"
#include "variable-load.h"


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
bool fee_enabled[3]                  = {false, false, false};
HardwareSerial* fee_ports[3]         = {UART_FIB_D, UART_FOB_D, UART_FSC_D};
const uint8_t sync_pins[3]           = {FIB_SYNC, FOB_SYNC, FSC_SYNC};
const uint8_t enable_pins[3]         = {EN_FIB, EN_FOB, EN_FSC};

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

bool init_uarts() {

  pinMode(UART_D, INPUT);
  pinMode(UART_S, INPUT);

  if(digitalRead(UART_D)) {
    // differential is enabled (positive enable)
    if(digitalRead(UART_S)) {
      // single-ended is not enabled (negative enable)
      fee_ports[0] = UART_FIB_D;
      fee_ports[1] = UART_FOB_D;
      fee_ports[2] = UART_FSC_D;
    } else {
      return false;
    }
  } else {
    // differential is not enabled (positive enable)
    if(digitalRead(UART_S)) {
      // single-ended is not enabled (negative enable)
      return false;
    } else {
      fee_ports[0] = UART_FIB_S;
      fee_ports[1] = UART_FOB_S;
      fee_ports[2] = UART_FSC_S;      
    }
  }
}

void fee_activate(uint8_t fee) {  
  if (fee < 3) {
    if(!fee_enabled[fee]) {
      digitalWrite(enable_pins[fee], HIGH);
      fee_ports[fee]->begin(BAUD_RATE);
      fee_enabled[fee] = true; 
    }
  }
}

void fee_deactivate(uint8_t fee) {
  if (fee < 3) {
    if(fee_enabled[fee]) {
      fee_ports[fee]->end();
      digitalWrite(enable_pins[fee], LOW);
      fee_enabled[fee] = false; 
    }
  }
}

void timer_isr() {
  uint16_t i;
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
   wait_us(PULSE_WIDTH_US, t_isr); 
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

  // every other time read from other adc
  adc_read_all(time_counter%2);
  
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

  // in order to initialize the data ring buffers for sci data
  init_sci_data();

  init_uarts();

  for(i=0; i<3; i++) {
    pinMode(sync_pins[i], OUTPUT);
    digitalWrite(sync_pins[i], LOW);
    pinMode(enable_pins[i], OUTPUT);
    digitalWrite(enable_pins[i], LOW);    
  }
  pinMode(CS0_PIN, OUTPUT);
  digitalWrite(CS0_PIN, HIGH);
  pinMode(CS1_PIN, OUTPUT);
  digitalWrite(CS1_PIN, HIGH);
  
  pinMode(DEBUG_PIN, OUTPUT);
  pinMode(ALIVE_PIN, OUTPUT); 
  Serial.begin(BAUD_RATE);
  SPI.begin();
  digitalWrite(ALIVE_PIN, HIGH);  
  set_load(0, 0); 
  set_load(1, 0); 
  Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
  // wait until we get one byte from the PC, so we sync the link
  while(true) {
    if(Serial.available()) {
      if(Serial.read() == 0x00) {
        break;
      }
    }
  }
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


