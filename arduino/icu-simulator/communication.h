#ifndef _communication_h
#define _communication_h

//************************ COMS SETTINGS *******************//
#define HK_CADENCE = 128;
#define SCI_CADENCE = 128;

#define CMD_PACKET_SIZE       6
#define REC_PACKET_SIZE       64

//************* SCI STRUCTURE **********//
#define SCI_HEADER_SIZE       10
#define FSC_SCI_SIZE          11
#define FIB_SCI_SIZE          10 
#define FOB_SCI_SIZE          10

// stay in multiples of 2 (we need at least 11)
// Ring buffer should be slightly larger anyways
// SCI CADENCE defines how many packets we need to store
// Be AWARE of using MACROS - brackets are your friend!
const unsigned int SCI_DATA_SIZE = (16*200);

//************* HK STRUCTURE **********//
#define HK_HEADER_SIZE      5
#define PCU_HK_SIZE         32
#define FIB_HK_SIZE         40 
#define FOB_HK_SIZE         4
#define FSC_HK_SIZE         53
#define HK_SIZE             HK_HEADER_SIZE + PCU_HK_SIZE + FIB_HK_SIZE + FOB_HK_SIZE + FSC_HK_SIZE + 2

// a bit of a hack, sci_queue enum should match up FEE numbering...
enum sci_queues {
  FIB_DATA=0,
  FOB_DATA=1,
  FSC_DATA=2,
  HEADER
};

union hk_packet_t {
  struct {
    byte pkt_length[2];
    byte id; 
    byte counter[4]; 
    byte pcu[PCU_HK_SIZE];
    byte fib[FIB_HK_SIZE];
    byte fob[FOB_HK_SIZE]; 
    byte fsc[FSC_HK_SIZE]; 
  };
  byte arr[HK_SIZE];
};

union sci_header_t {
  struct {
    byte pkt_length[2]; 
    byte id; 
    byte counter[4]; 
    byte n[3];
  };
  byte arr[SCI_HEADER_SIZE];
};

typedef struct sci_data_t {
  unsigned int tail; // ring bufer tail
  unsigned int head; // ring buffer head
  unsigned int n; // number of science data sets in the buffer
  byte data[SCI_DATA_SIZE];
};

// low level communication functions to talk to FEEs
void create_cmd_packet(uint8_t * command);
void send_fee_cmd(HardwareSerial * port, int fee);
void receive_fee_response(HardwareSerial * port, int fee);
bool process_fee_response(uint8_t fee);

// higher level communication functions to talk to PC
void init_sci_data();
uint8_t checksum(uint8_t * arr, int l);
void init_sci_packet(unsigned long t);
void init_hk_packet(unsigned long t);
bool send_sci_packet();
bool send_hk_packet();
#endif /* !defined _adc_h */
