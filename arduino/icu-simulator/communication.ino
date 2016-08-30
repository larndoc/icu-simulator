#include "communication.h"
#include "adc.h"
uint8_t default_fee_cmd[CMD_PACKET_SIZE] = {0x01,0x00,0x00,0x00,0x00,0x01};
uint8_t fee_cmd[3][CMD_PACKET_SIZE];
uint8_t fee_rec[3][REC_PACKET_SIZE];
uint8_t fee_rec_counter[3] = {0,0,0};
enum sci_queues sci_queue = HEADER;
int sci_send_counter = 0;
int hk_send_counter = 0; 

uint8_t fee_sci_sizes[3] = {
  FIB_SCI_SIZE, 
  FOB_SCI_SIZE, 
  FSC_SCI_SIZE
};

int fee_sci_to_send[3] = {0,0,0};

uint8_t fee_hk_sizes[3] = {
  FIB_HK_SIZE, 
  FOB_HK_SIZE, 
  FSC_HK_SIZE
};
uint8_t * cmd_packet[3] = {
  default_fee_cmd,
  default_fee_cmd,
  default_fee_cmd
};


sci_header_t sci_header;
hk_packet_t hk_packet;
sci_data_t sci_data[3];

void init_sci_data() {
  int i;
  for(i=0;i<3;i++) {
    sci_data[i].tail=0;
    sci_data[i].head=0;
    sci_data[i].n=0;
  }
}

/* create_cmd_packet(arr):
 *  inteprets arr and creates a new command packet for 
 *  the corresponding fee (first byte in arr)
 */
void create_cmd_packet(uint8_t * command) {
  uint8_t index = command[0];
  int j = 2;
  fee_cmd[index][0] = 0x00;
  if (command[1] == 0) {
    fee_cmd[index][0] |= 0x03;
  } else if (command[1] == 1) {
    fee_cmd[index][0] |= 0x05;
  }
  for (int i = 1; i < 5; i++, j++) {
    fee_cmd[index][i] = command[j];
  }
  fee_cmd[index][5] = 0; /* here we will build our checksum */
  for (int i = 0; i < 5; i++) {
    fee_cmd[index][5] ^= fee_cmd[index][i];
  }
  // set this at last, to avoid conflicts
  cmd_packet[index] = fee_cmd[index];
}

/* send_fee_packet(&port, fee):
 *  sends a command packet to fee on port.
 *  resets command packet to default cmd after execution
 */
void send_fee_cmd(HardwareSerial * port, int fee) {
  port->write(cmd_packet[fee], CMD_PACKET_SIZE);
  cmd_packet[fee] = default_fee_cmd;
}

/* receive_fee_response(&port, ree):
 *  If one byte is available on the serial port, this function
 *  appends it to arr[n] and increments n
 */
void receive_fee_response(HardwareSerial * port, int fee) {
  if(port->available()) {
    if(fee_rec_counter[fee] < REC_PACKET_SIZE) {
      fee_rec[fee][fee_rec_counter[fee]] = port->read();
      fee_rec_counter[fee]++;
    }
  }
}


/* process_fee_response(fee):
 *  copies the dataframes "Sci" and "HK" from the
 *  received response to the defined storage spaces
 *  returns true if that goes ok.
 */
bool process_fee_response(uint8_t fee) {
  uint8_t i;
  uint8_t sci_size = fee_sci_sizes[fee];
  uint8_t hk_size = fee_hk_sizes[fee];
  uint8_t data_size = 1+sci_size+hk_size+5;
  uint8_t *arr = fee_rec[fee];
  byte* hk_data;
  // prepare data frames to write into
    
   switch(fee) {
    case 0:
      hk_data = hk_packet.fib;
      break;
    case 1:
      hk_data = hk_packet.fob;
      break;
    case 2:
      hk_data = hk_packet.fsc;
      break;
    default:
      // got a wrong FEE number (not 0, 1 or 2)
      return false;
  }

  if(fee_rec_counter[fee] < data_size) {
    // error, TBD to do
  }
  
  // calculate checksum over length of packet
  if( checksum(arr, data_size) ) {
    // don't do anything yet
  }
  // reset receive buffer counter when processing
  fee_rec_counter[fee]=0;

  // start decoding the packet
  if((*arr == 0x00) || true) {
    // status byte is ok, so we copy over the data
    arr++; // go to science data start
    // append science data to ring buffers
    for(i=0; i<sci_size; i++, arr++) {
      sci_data[fee].data[sci_data[fee].head] = *arr;
      sci_data[fee].head = (sci_data[fee].head+1)%SCI_DATA_SIZE;
      // might include check if head is still bigger tail
    }
    sci_data[fee].n++;
    // copy over housekeeping
    for(i=0; i<hk_size; i++, arr++) {
      hk_data[i] = *arr;
    }
    // config parmater id and config paramater value are thrown away for now
    for(i=0; i<4; i++, arr++) {
      // throw away config id and params
    }
    return true;    
  } else {
    // FEE flags error, TBD what to really do (ask Peter)   
    return false;
  }
}

/* checksum(arr, length):
 *  calculates a checksum over the arr.
 */
uint8_t checksum(uint8_t * arr, int l) {
  uint8_t c = 0;
  while(l--) {
    c ^= *arr;
    arr++;
  }
  return c;
}

/* init_sci_packet(t):
 *  initializes the science packet with timestamp t
 *  at this point whatever is in the ring buffer for science data
 *  will be taken for sending
 */
void init_sci_packet(unsigned long t) {
  // initialize the sci header...
  int i;
  uint8_t total_size = 0x00;
  sci_header.id = 0x01;  
  byte* counter_ptr = sci_header.arr;
  copy_timestamp(counter_ptr, t); 
  for(i=0;i<3;i++) {
    sci_header.n[i] = sci_data[i].n;
    // calculate bytes to send for each fee science data frame
    // as this can change, we cannot use a #define as for hk or 
    // the sci header.
    fee_sci_to_send[i] = sci_header.n[i]*fee_sci_sizes[i];
    // reset ring buffer n, counting new sci data now
    sci_data[i].n = 0;
  }
  for(int i = 0; i<3; i++){
    total_size += fee_sci_to_send[i];
  }
  sci_header.pkt_length[0] = total_size >> 8;
  sci_header.pkt_length[1] = total_size; 
}

/* init_sci_packet(t):
 *  initializes the hk packet with timestamp t
 */
void update_hk(){
  byte p_loc[32];
  adc_read_all(1, p_loc); 
  adc_read_all(0, p_loc + 16); 
  hk_packet.pkt_length[0] = HK_SIZE >> 8;
  hk_packet.pkt_length[1] = HK_SIZE; 
  int i, j; 
  for(i = 0, j = 31; i < 32; i++, j--){
    hk_packet.pcu[i] = p_loc[j]; 
  }
}
void init_hk_packet(unsigned long t) {
  update_hk();
  hk_packet.id = 0x00;
 
  byte* counter_ptr = hk_packet.arr;
  copy_timestamp(counter_ptr, t); 
}

/* send_sci_packet():
 *  tries to send (as many) bytes from the sci_packet as possible without blocking
 *  another call of the function will continue sending
 *  whilst sending is still ongoing, the function returns true
 *  once sending is complete, the function returns false
 */
bool send_sci_packet() {
  // start a sending queue, first header, then body
  switch(sci_queue) {
    case HEADER:
      if(Serial.availableForWrite()) {
        Serial.write(sci_header.arr[sci_send_counter]);
        sci_send_counter++;
      }
      break;
    case FIB_DATA:
    case FOB_DATA:
    case FSC_DATA:
      // make sure we can write to the port and the buffer has values to write
      if(Serial.availableForWrite() && (sci_send_counter < fee_sci_to_send[sci_queue])) {
        Serial.write(sci_data[sci_queue].data[sci_data[sci_queue].tail]);
        sci_data[sci_queue].tail = (sci_data[sci_queue].tail + 1) % SCI_DATA_SIZE;
        sci_send_counter++;
      }
      break;
  }
   
  // swtich dataframes if needed
  switch(sci_queue) {
    case HEADER:
      if(sci_send_counter >= SCI_HEADER_SIZE) {
        sci_queue = FIB_DATA;
        sci_send_counter = 0;
      }
      break;
    case FIB_DATA:
      if(sci_send_counter >= fee_sci_to_send[0]) {
        sci_queue = FOB_DATA;
        sci_send_counter = 0;
      }
      break;
    case FOB_DATA:
      if(sci_send_counter >= fee_sci_to_send[1]) {
        sci_queue = FSC_DATA;
        sci_send_counter = 0;
      }
      break;
    case FSC_DATA:
      if(sci_send_counter >= fee_sci_to_send[2]) {
        sci_queue = HEADER;
        sci_send_counter = 0;
      }
      break;
  }
  // we are back to start of dataframe, so we finished sending
  if((sci_queue == HEADER) && (sci_send_counter == 0)) return false;
  else return true;
}

/* send_hk_packet():
 *  tries to send (as many) bytes from the hk_packet as possible without blocking
 *  another call of the function will continue sending
 *  whilst sending is still ongoing, the function returns true
 *  once sending is complete, the function returns false
 */
bool send_hk_packet() {
  if(hk_send_counter < HK_SIZE) {
    if(Serial.availableForWrite()) {        
      Serial.write(hk_packet.arr[hk_send_counter]);
      hk_send_counter++;
    }
    return true;
  } else {
    hk_send_counter = 0;
    return false;
  }  
}

void copy_timestamp(byte* arr, unsigned long t){
  int i = 5; 
  while(i > 1){
    arr[i] = (0x000000FF & t); 
    t = t >> 8;
    i--; 
  } 
}

