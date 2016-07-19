#ifndef PACKETS_H
#define PACKETS_H

#define BYTE_SIZE 8
#define PACKET_SIZE 6
#define PACKETS_TO_TRANSFER 3 
#define BAUD_RATE 115200 
#define FEE_PACKET_SIZE 100 
#define PACKETS_RECIEVED 3
//// easiest way to initialise the command packet
//uint8_t cmd_packet[3][PACKET_SIZE];
//
//// easiest way to intitalise the response packet
//uint8_t response_packet[3][RESPONSE_PACKET_SIZE];
//// how to access the individual bytes
//response_packet[0][counter] = 0;
//
//// doing it slightly more cmoplicated
//
//struct cmd_packet {
//  uint8_t bytes[PACKET_SIZE]
//}
//
//cmd_packet fee[3];
//
//fee[0].bytes[counter]
//
//// response_packet coutners
uint8_t response_packet_counter[3]; //this counts the number of fee packets from each of the three interfaces, need to increment the packets for each of the response packets that are recieved...


struct byte_r{
  int data; 
};
struct packet{
  byte bytes [PACKET_SIZE];
};

struct response_packet{
  int bytes [FEE_PACKET_SIZE];                          //assuming the maximmum size of the response packet is given by the macro FEE_PACKET_SIZE, if overflow need to trigger an error message for that.. 
};

struct fee_interface{
   response_packet rep_packet[PACKETS_RECIEVED]; 
};

struct interface_cmd_packets{
  packet packets[PACKETS_TO_TRANSFER]; 
};
#endif

