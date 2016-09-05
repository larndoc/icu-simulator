/*
 * the program allows the ICU - Simulator to conduct 
 * a sequence of tasks including transmission of 
 * command packets to the UART interfaces and 
 * reception and processing of any previous FEE responses.
 * It also allows the user to command the FEE such as 
 * switching the heater on/off. The variable time_counter 
 * is a measure of the number of pulses that were genereted since 
 * we entered the science or config mode. 
 * We initiate our timer interrupt 
 * service routine, in the setup with a frequency of 
 * 128 Hz(defined by FREQUENCY). 
 * Here we will:  
 * a)generate our synchronisation signals for the three UART interaces(FIB, FOB and FSC) 
 * b) if we are in science mode and an ICU command packet was sent, process any previous fee responses 
 * c) set the flag to recieve fee response and house keeping response only if SCI_CADENCE and HK_CADENCE % time that has elapsed since the 
 *    we entered CONFIG or SCIENCE MODE has a numeric value of zero.
 * d) send fee command if we are in science mode. 
 * e) call the adc_read_all function if we are not in standby mode for every other ADC. 
 * f) reset time_counter to zero if we are in standby mode, only start counting total number of pulses generated if we go to either SCIENCE or CONFIG MODE.  
 * This means that the science packet is recieved with a cadence of 
 * SCI_CADENCE and house keeping packet is recieved
 * with a cadence of HK_CADENCE, both of which are defined in communication.h
 * There are a total of three modes, the user does not recieve any data in STANDY MODE, 
 * the user recieves both science and house keeping data in SCIENCE_MODE, and the user 
 * only recieves house keeping data in CONFIG_MODE. 
 * The default mode is set to standby mode and we do not begin recieving any data unless we 
 * go to either SCIENCE or CONFIG mode. 
 * 
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

/*modes for the state machine that is implemented by inside the loop function, the inputs for the state machine are external*/ 
enum icu_modes {
  STANDBY_MODE=0,
  SCIENCE_MODE,  
  CONFIG_MODE,  
};

/*set the default mode to the standby mode, the user will not being recieving any data unless he goes to either config or science mode*/ 
enum icu_modes mode  = STANDBY_MODE;
bool fee_enabled[3]                  = {false, false, false}; 
HardwareSerial* fee_ports[3]         = {UART_FIB_D, UART_FOB_D, UART_FSC_D}; //UART interfaces in differential mode 

/*tx and rx pins for the interfaces, these will be used inside the activate function, i.e set high, can not use fee_ports->begin() and fee_ports->end() because if a fee_port is deactivated, we can not set the tx/rx pins high again */
uint8_t tx_pins[3]                   = {FIB_TX_D, FOB_TX_D, FSC_TX_D};
uint8_t rx_pins[3]                   = {FIB_RX_D, FOB_RX_D, FSC_RX_D};
const uint8_t sync_pins[3]           = {FIB_SYNC, FOB_SYNC, FSC_SYNC}; //sync signals for FIB, FOB and FSC interface
const uint8_t enable_pins[3]         = {EN_FIB, EN_FOB, EN_FSC}; //flags used to activate or de-activate an interface

uint32_t time_counter = 0;
unsigned long t_isr;

bool cmd_packet_sent = false;
bool send_hk = false; 
bool send_sci = false; 
bool sending_hk = false; 
bool sending_sci = false;
 
byte user_cmd = 0xFF; //the default user_cmd is 0xFF, we will use this value if as default
uint8_t user_fee_cmd[6] = {0}; //arry for storing the commnd that the user can give to a FEE

/*
 * the way that the wait function works, 
 * is we stay in the loop until the time 
 * that has elapsed in micro seconds since 
 * we have set the sync signal high is 
 * greater than delta_us which is the desired 
 * waiting time, and is defined by the variable 
 * PULSE_WIDTH_US 
 */
void wait_us(unsigned long delta_us, unsigned long t) {
  while ( (micros()  - t ) < delta_us ) {
    if (micros() - t < 0) {      
      delta_us = delta_us - (0xFFFFFFFF - t);
    }
  }
}

void init_uarts() {
  int i;
  bool old_en[3];

  pinMode(UART_D, INPUT);
  pinMode(UART_S, INPUT);

  // deactivate all fees
  for(i=0; i<3; i++) {
    old_en[i] = fee_enabled[i];
    fee_deactivate(i);
  }

  if(digitalRead(UART_S)) {
    // single-ended is not enabled (negative enable)
    // activate ports for differential comms
    fee_ports[0] = UART_FIB_D;
    fee_ports[1] = UART_FOB_D;
    fee_ports[2] = UART_FSC_D;
    tx_pins[0] = FIB_TX_D;
    tx_pins[1] = FOB_TX_D;
    tx_pins[2] = FSC_TX_D;
    rx_pins[0] = FIB_RX_D;
    rx_pins[1] = FOB_RX_D;
    rx_pins[2] = FSC_RX_D;    
  } else {
    // single-ended is enabled
    if(digitalRead(UART_D)) {
      // differential is enabled (positive enable)
      // don't do anyting - kind of an error condition
    } else {
      // differential is disabled
      fee_ports[0] = UART_FIB_S;
      fee_ports[1] = UART_FOB_S;
      fee_ports[2] = UART_FSC_S;      
      tx_pins[0] = FIB_TX_S;
      tx_pins[1] = FOB_TX_S;
      tx_pins[2] = FSC_TX_S;      
      rx_pins[0] = FIB_RX_S;
      rx_pins[1] = FOB_RX_S;
      rx_pins[2] = FSC_RX_S;            
    }
  }

  // re-activate all fees
  for(i=0; i<3; i++) {
    if(old_en[i]) {
      fee_activate(i);
    }
  }
  
}

void pcu_activate() {
  digitalWrite(CS0_PIN, HIGH);
  digitalWrite(CS1_PIN, HIGH);
  SPI.begin();
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));

}

void pcu_deactivate() {
  digitalWrite(CS0_PIN, LOW);
  digitalWrite(CS1_PIN, LOW);
  SPI.endTransaction();
  SPI.end();
}

void fee_activate(uint8_t fee) {  
  uint8_t usart=fee;
  if (fee < 3) {
    if(fee_enabled[fee] == false) {
      digitalWrite(DEBUG_PIN, HIGH);
      digitalWrite(enable_pins[fee], HIGH);
      // here comes a big hack to sort out usart configuration after pinMode has been used... 
      if(!digitalRead(UART_D) && !digitalRead(UART_S)) {
        // single ended enabled and not differential enabled
        switch(fee) {
          case 0: usart = 2; break;
          case 1: usart = 0; break;
          case 2: usart = 1; break;
        }
      }
      // uses stuff from variant.cpp from arduino SAM boards library, as 
      // the pinMode seems to have a bug, where it is not possible to use
      // a pin as output and afterwards configure it for USART
      // ---
      switch(usart) {
        case 0:
        PIO_Configure(
          g_APinDescription[PINS_USART0].pPort,
          g_APinDescription[PINS_USART0].ulPinType,
          g_APinDescription[PINS_USART0].ulPin,
          g_APinDescription[PINS_USART0].ulPinConfiguration);        
        break;
        case 1:
        PIO_Configure(
          g_APinDescription[PINS_USART1].pPort,
          g_APinDescription[PINS_USART1].ulPinType,
          g_APinDescription[PINS_USART1].ulPin,
          g_APinDescription[PINS_USART1].ulPinConfiguration);        
        break;
        case 2:
        PIO_Configure(
          g_APinDescription[PINS_USART3].pPort,
          g_APinDescription[PINS_USART3].ulPinType,
          g_APinDescription[PINS_USART3].ulPin,
          g_APinDescription[PINS_USART3].ulPinConfiguration);        
        break;        
      }
      fee_ports[fee]->begin(BAUD_RATE);
      fee_enabled[fee] = true; 
    }
  }
}

void fee_deactivate(uint8_t fee) {
  if (fee < 3) {
    if(fee_enabled[fee]) {
      digitalWrite(DEBUG_PIN, LOW);
      fee_ports[fee]->end();
      pinMode(tx_pins[fee], OUTPUT);
      digitalWrite(sync_pins[fee], LOW);
      digitalWrite(enable_pins[fee], LOW);
      fee_enabled[fee] = false; 
    }
  }
}

void timer_isr() {
 if(mode == STANDBY_MODE){
  time_counter = 0;
 } else {
  uint16_t i;
  time_counter++;
  t_isr = micros(); 

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
  
  // every other time read from other adc
  adc_read_all(time_counter%2);
  
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
 }
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

  for(i=0; i<3; i++) {
    pinMode(sync_pins[i], OUTPUT);
    pinMode(enable_pins[i], OUTPUT);
    pinMode(tx_pins[i], OUTPUT);
  }

  init_uarts();
    
  pinMode(CS0_PIN, OUTPUT);
  pinMode(CS1_PIN, OUTPUT);
  
  pinMode(DEBUG_PIN, OUTPUT);
  pinMode(ALIVE_PIN, OUTPUT); 
  SerialUSB.begin(BAUD_RATE);
  set_load(0, 0); 
  set_load(1, 0); 
  digitalWrite(ALIVE_PIN, HIGH);    
  Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
  attachInterrupt(digitalPinToInterrupt(UART_S), init_uarts, CHANGE); // trigger init_uarts function whenever UART_S pin changes
}

void loop() {

  // stuff to do all the time
  // 1) check for external input from PC
  // 2) send HK data
  // 3)
   
  switch(user_cmd) { 
    case 0x00:
      // make sure pcu is deactivated
      pcu_deactivate();
      mode = STANDBY_MODE;
      user_cmd = 0xFF;  
      break;
    case 0x03:
      // make sure pcu is active
      pcu_activate();
      mode = SCIENCE_MODE; 
      user_cmd = 0xFF;
      break; 

    case 0x02:
      // serial input buffer should be bigger than 6
      if(SerialUSB.available() >= 6) {
        SerialUSB.readBytes(user_fee_cmd, 6);
        create_cmd_packet(user_fee_cmd); 
        user_cmd = 0xFF;
      }
      //the input remains the same, if we are in science mode we stay in science mode and if we are in config mode, then we stay in config mode, hence it is not required to update the input  
      break; 
  case 0x04:
    // make sure pcu is active
    pcu_activate();
    mode = CONFIG_MODE;
    user_cmd = 0xFF;
    break;

  
  case 0x05:
    if(SerialUSB.available()) {
      if(mode == CONFIG_MODE) {
        // only in config mode activate an fee
        fee_activate(SerialUSB.read());
      } else {
        // just read and throw away otherwise
        SerialUSB.read();
      }
      user_cmd = 0xFF;
    }
    break; 

  
  case 0x06: 
    if(SerialUSB.available()) {
      if(mode == CONFIG_MODE) {
        fee_deactivate(SerialUSB.read());   
      } else {
        // just read and throw away otherwise
        SerialUSB.read();
      }
      user_cmd = 0xFF;
    }
    break; 

  default:
    // if no user command was set, check for a new one
    if(SerialUSB.available()) {
      user_cmd = SerialUSB.read();
    }
  }

  // send Sci data, if not already sending HK data
   if(send_sci && !sending_hk) {
     if(send_sci) digitalWrite(DEBUG_PIN, HIGH);
     sending_sci = send_sci_packet();
     // this will reset the send_sci flag once sending is done
     send_sci = sending_sci;
     if(!send_sci) digitalWrite(DEBUG_PIN, LOW);
   } else {
    // only HK send if Sci is not sending already
    if(send_hk && !sending_sci){
      sending_hk = send_hk_packet();
      // this will reset the send_hk flag once sending is done
      send_hk = sending_hk;
    }    
   }

  // receive fee responses, if we sent a command
  if(cmd_packet_sent){
    for (int i = 0; i < 3; i++) {
      if(fee_enabled[i]){
        receive_fee_response(fee_ports[i], i);
      }
    }
  }   

  // state machine of the ICU
  switch (mode) {   
    case STANDBY_MODE:

      break;
    case CONFIG_MODE: 
      // nothing to do in CONFIG MODE yet     
      break; 
    case SCIENCE_MODE:

      break; 
  }
} // loop ends



