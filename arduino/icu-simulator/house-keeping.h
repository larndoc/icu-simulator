

#pragma pack (1)
#include "adc.h"
#define PCU_DATA_SIZE   32
#define FIB_HK_SIZE     40 
#define FOB_HK_SIZE     4
#define FSC_HK_SIZE     (8 + 6*16 + 2*24 + 2*16 + 24 + 12*16 + 8)/8
#define TOTAL_HK_SIZE    5 + PCU_DATA_SIZE + FIB_HK_SIZE + FOB_HK_SIZE + FSC_HK_SIZE  


union house_keeping
{
struct

{
	byte id; 
	unsigned long sync_counter; 
	uint16_t adc_readings[NUM_ADCS][8];
	byte fib_hk[FIB_HK_SIZE];
	byte fob_hk[FOB_HK_SIZE]; 
	byte fsc_hk[FSC_HK_SIZE]; 
};
	byte arr[TOTAL_HK_SIZE];

};
