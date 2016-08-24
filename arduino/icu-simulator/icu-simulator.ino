/* in order to reject any noise interference the appropiate boolean values for the variable fee_enabled need to be set */ 
/*currently serial1 is configured to the synchronisation pin at pin 11, serial2 is configured to the synchronisation pin at pin 13 and serial is configured to the synchromnisation pin at pin 12 */ 
  #include <DueTimer.h>
  #include <time.h>
  #include <stdlib.h>
  #include "adc.h"
  #include "errors.h"
  #include "fee_packet_structure.h"
  #include "pc_data_dump.h"
  #include "house-keeping.h"
  #include <SPI.h>
  
  #define BUFFER_SIZE           3
  //********************************************************************************CLOCK INFORMATION****************************************************************//
  #define FREQUENCY             128
  #define PULSE_WIDTH_US        1000
  #define PERIOD_US             100000/FREQUENCY
  #define BAUD_RATE             115200
  
  //******************************************************************************GLOBAL VARIABLES***************************************************************//

  /*set of states that the user transverses through based on the input(which can be intrinsic or defined by the user(external)*/ 
  enum set {
    SCIENCE_MODE=0,  
    CONFIG_MODE,  
    };
  enum set task  = CONFIG_MODE;
  /*fee packet and pointer to the three fee_packets, the data structure used for fee_packet is a union which is included in the folder fee_packet_structure*/ 
  int buffer_index = 0; 
  fib_paket fib_pack[BUFFER_SIZE]; 
  fob_packet fob_pack[BUFFER_SIZE]; 
  fsc_packet fsc_pack[BUFFER_SIZE]; 
  /*declaration of the pc packet, used to package the recieved bytes from the three interfaces and write it out the serial port, the struct used for pc packet is a union defined in pc_data_dump.h */
  pc_data pc_packet  =  {0x01, 1};       
  byte pc_packet_arr[BUFFER_SIZE * 64];
  
  house_keeping hk_pkt;
  
  /*a 2-D (3 x 6) array for the command packets that includes the command packet to be sent to each interface */ 
  uint8_t response_packet_counter[3]   = {0, 0, 0};
  bool checksum[3]                     = {false, false, false};
  bool fee_enabled[3]                  = {false, false, false};
  HardwareSerial* port[3]              = {&Serial1, &Serial2, &Serial3};
  const uint8_t sync_pins[3]           = {11, 13, 12};
  bool hk_send = false; 
  const uint8_t debug_pin    = 10; 
  uint32_t current_time;
  uint32_t t;
  bool overflow = false;
  uint32_t time_counter            = 0;
  bool packet_sent = false;
  bool packet_processed = false;
  int size_of_pc_packet = 0; 
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
  
  void wait_us(unsigned long delta_us) {
    while ( (micros()  - t ) < delta_us ) {
      /*indicates whether a overflow has occured 
       * the time t is declared as a global variable which is of eight bytes 
       * if micros() < t we can deduce that a overflow has occured, so we need to wait for the amount of time given by delta_us(total waiting time) - (0xFFFFFFFF - t) 
       */
      if (micros() - t < 0) {      
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
    time_counter++;
    if(time_counter % 128 == 0){
      hk_send = true; 
    }
    if(task == SCIENCE_MODE) {
      pc_packet.sync_counter = int32_t(__builtin_bswap32(time_counter));
      t = micros();
      // take the time (currently only sync counter) when we have sent the sync pulse 
    
      for(int i = 0; i < 3; i++){
        if(fee_enabled[i]){
          digitalWrite(sync_pins[i], HIGH);         //setting up of the pins 
        }
      }
    }
        if((fee_enabled[0] || fee_enabled[1] || fee_enabled[2]) && (buffer_index == 0)){
          size_of_pc_packet = 8; 
          /*status byte*/
          pc_packet_arr[0] = 0x01; 
          pc_packet_arr[1] = pc_packet.arr[1]; 
          pc_packet_arr[2] = pc_packet.arr[2]; 
          pc_packet_arr[3] = pc_packet.arr[3]; 
          pc_packet_arr[4] = pc_packet.arr[4];
        }
        
        if(packet_sent) {
        // only if a packet has been sent in the previous timer_isr()
        // we will try and process packets from enabled FEEs    
        packet_sent = false;
        
        
        for(int i = 0; i < 3; i++){
          if(fee_enabled[i]){
            process_packet(i); 
          }
        }
        if(fee_enabled[0] || fee_enabled[1] || fee_enabled[2]){
          buffer_index++;   
        }
        if(buffer_index == BUFFER_SIZE){
            packet_processed = true; 
            buffer_index = 0; 
        }
    }
 
  
    if(task == SCIENCE_MODE) { 
      wait_us(PULSE_WIDTH_US);   
      for(int i = 0; i < 3; i++){
        if(fee_enabled[i]){
          send_packet(port[i], i);
        }
      }
      packet_sent = true;
      for (int i = 0; i < 3; i++) {
        if (fee_enabled[i]) {
          digitalWrite(sync_pins[i], LOW);
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
    pinMode(41, OUTPUT);
    pinMode(debug_pin, OUTPUT);
    Serial.begin(BAUD_RATE);
    SPI.begin(); 
    for (int i = 0; i < 3; i++) {
      if (fee_enabled[i]) {
        pinMode(sync_pins[i], OUTPUT);
        digitalWrite(sync_pins[i], LOW);
        port[i]->begin(BAUD_RATE);
      }
    }
    Timer.getAvailable().attachInterrupt(timer_isr).setFrequency(FREQUENCY).start();        /*attach the interrupt to the function timer_isr at 128 Hz (FREQUENCY)*/
  }
  
  void check_checksum(int index)
  {
    /*
    if (fib_pack[buffer_index].arr[FEE_PACKET_SIZE - 1] != checksum[index])
    {
      fee_packet[index][buffer_index].arr[0] = INVALID_ICU_PACKET_CHECKSUM;
    }
    */
  
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
              create_cmd_packet(fee_command); 
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
        task = CONFIG_MODE;       
       break; 
  
  /*****************************************************************************************************************************SCIENCE MODE*****************************************************************************************************************************/
     /*
      * in science mode, we check to see if the packet has been sent and processed, if the packet has been sent, we listen for any incoming data on the three FEEs
      * processing of the packet allows us to determine whether the data in the packet is good/bad, if the data is good, we package it for sending to the pc. We check to see if a packet exists, and if it does not exist we set the n_fib/n_fob/n_fsc back to zero.
      * the science data for FIB and FOB is 10, whereas the size of the science data for FSC is set to 11 
      */
      
      
      case SCIENCE_MODE:
      { 
        if(packet_sent){
          for (int i = 0; i < 3; i++) {
            if(fee_enabled[i]){
              check_port(port[i], i);
            }
          }
        }
        if(packet_processed){ 
          packet_processed = false; 
          Serial.write(pc_packet.arr, 5);  
         }
         break; 
      }
  /******************************************************************************************************************************PC_TRANSMIT*********************************************************************************************************************************/

      default:
        task = CONFIG_MODE;
    }

    /*
     * the flag is only set every 128th tick of the clock, we prepare our house keeping packet and transmit it
     */

      if( hk_send == true){
          hk_send = false; 
          /*now we must prepare our house keeping packet*/
          hk_pkt.id = 0x00; 
          hk_pkt.sync_counter = uint32_t (__builtin_bswap32(time_counter));
        
          adc_read_all(ADC_VSENSE); 
          adc_read_all(ADC_ISENSE);
        
        for(int i = 0; i < 8; i++){
          hk_pkt.adc_readings[ADC_VSENSE][i] = adc_readings[ADC_VSENSE][i]; 
          hk_pkt.adc_readings[ADC_ISENSE][i] = adc_readings[ADC_ISENSE][i];
        }
        
        if(task == CONFIG_MODE){
          
          
          for(int i = 0; i < FIB_HK_SIZE; i++){
            hk_pkt.fib_hk[i] = 0; 
          }
          for(int i = 0; i < FOB_HK_SIZE; i++){
            hk_pkt.fob_hk[i] = 0; 
          }
          for(int i = 0; i < FSC_HK_SIZE; i++){
            hk_pkt.fsc_hk[i] = 0; 
          }
        }

        else if(task == SCIENCE_MODE){
          /* 
           *  the zeroeth byte of the fib and fob house keeping should be the last byte of the science data, because the length of science_data has been set to 11
           */
            for(int i = 0; i < FIB_HK_SIZE; i++){
              hk_pkt.fib_hk[i] =  fib_pack[buffer_index].hk_data[i];
            }
          
            for(int i = 0; i < FOB_HK_SIZE; i++){
              hk_pkt.fob_hk[i] =  fob_pack[buffer_index].hk_data[i];
            }
            
          for(int i = 1; i < FSC_HK_SIZE;i++){
            hk_pkt.fsc_hk[i] = fsc_pack[buffer_index].hk_data[i];
          }
        }
         // Serial.write(hk_pkt.arr, TOTAL_HK_SIZE); 
       }
   
  }
  
  void fee_activate(int index){
    
    if ( index > 2 || index < 0){
        return;  
    }
    else{
        activate_pins(index); 
        fee_enabled[index] = true; 
        pc_packet_arr[5 + index] += 1;
    }
  }
  
  
  void fee_deactivate(char index){
    if ((index) > 2 || (index) < 0){
      return; 
    }
    else{
      deactivate_pins(index); 
    fee_enabled[index] = false; 
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

