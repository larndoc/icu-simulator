#define CMD_PACKET_SIZE 6
#define FSC_SCI_DATA_LENGTH               11
#define FIB_SCI_DATA_LENGTH               10 
#define FOB_SCI_DATA_LENGTH               10 
#define FIB_HOUSE_KEEPING_DATA_LENGTH     40 
#define FOB_HOUSE_KEEPING_DATA_LENGTH     4
#define FSC_HOUSE_KEEPING_DATA_LENGTH     53
uint8_t default_fee_cmd[CMD_PACKET_SIZE] = {0x01,0x00,0x00,0x00,0x00,0x01};
uint8_t fee_sizes[3] = {FIB_SCI_DATA_LENGTH, FOB_SCI_DATA_LENGTH, FSC_SCI_DATA_LENGTH};
uint8_t fee_hk_sizes[3] = {FIB_HOUSE_KEEPING_DATA_LENGTH, FOB_HOUSE_KEEPING_DATA_LENGTH, FSC_HOUSE_KEEPING_DATA_LENGTH};
uint8_t fee_cmd[3][CMD_PACKET_SIZE];

uint8_t * cmd_packet[3] = {
  default_fee_cmd,
  default_fee_cmd,
  default_fee_cmd
};

bool process_hk_packet()
{
  hk_pkt.arr[0] = 0x00;
  hk_pkt.arr[4] = time_counter; 
  hk_pkt.arr[3] = time_counter >> 8;
  hk_pkt.arr[2] = time_counter >> 16; 
  hk_pkt.arr[1] = time_counter >> 24 ;
  adc_read_all(ADC_VSENSE);
  adc_read_all(ADC_ISENSE);
  for (int i = 0; i < 8; i++) {
    hk_pkt.adc_readings[ADC_VSENSE][i] = adc_readings[ADC_VSENSE][i];
    hk_pkt.adc_readings[ADC_ISENSE][i] = adc_readings[ADC_ISENSE][i];
  }
  return true;
}


bool process_sci_packet()

{
  for (int i = 0; i < 3; i++) {
      response_packet_counter[i] = 0;
  }
  buffer_index++;
  if (buffer_index == SCIENCE_BUFFER_SIZE) {
    buffer_index = 0;
    packet_processed = true;
    return true;
  } else {
    return false;
  }
}

void create_cmd_packet(uint8_t * command)
{
  uint8_t index = command[0];
  int j = 2;
  cmd_packet[index] = fee_cmd[index];
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
}

void send_packet(HardwareSerial * port, int index)
{

  port -> write(cmd_packet[index], CMD_PACKET_SIZE);
  cmd_packet[index] = default_fee_cmd;
}
  
void configure_port(HardwareSerial * port, int index)
{
    if(port->available()){
      if(index == 0){
        if(size_of_fee_packet < 14){
          pc_packet_arr[size_of_pc_packet] = port->read();
        }
        else if(size_of_fee_packet < 14 + FIB_HOUSE_KEEPING_DATA_LENGTH){
          hk_pkt.fib_hk[i] = port->read(); 
        }
        else if(size_of_fee_packet < 18 + FIB_HOUSE_KEEPING_DATA_LENGTH){
          byte tail = port->read(); 
        }
      }
      else if(index == 1){
        if(size_of_fee_packet < 14){
          pc_packet_arr[size_of_pc_packet + 10] = port->read(); 
        }
         else if(size_of_fee_packet < 14 + FOB_HOUSE_KEEPING_DATA_LENGTH){
          hk_pkt.fob_hk[i] = port->read(); 
        }
        else if(size_of_fee_packet < 18 + FOB_HOUSE_KEEPING_DATA_LENGTH){
          byte tail = port->read(); 
        } 
      }
      else if(index == 2){
        if(size_of_fee_packet < 15){
          pc_packet_arr[size_of_pc_packet + 20] = port->read(); 
        }
         else if(size_of_fee_packet < 15 + FIB_HOUSE_KEEPING_DATA_LENGTH){
          hk_pkt.fib_hk[i] = port->read(); 
        }
        else if(size_of_fee_packet < 19 + FIB_HOUSE_KEEPING_DATA_LENGTH){
          byte tail = port->read(); 
        }
      }
}
}
