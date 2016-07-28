#ifndef PC_DATA_DUMP_H
#define PC_DATA_DUMP_H

#define FIB_SCI_DATA_SIZE   10
#define FOB_SCI_DATA_SIZE   10
#define FSC_SCI_DATA_SIZE   10
#define N_FIB               0
#define N_FOB               1
#define N_FSC               0
#define TOTAL_FIB_SIZE      N_FIB*FIB_SCI_DATA_SIZE
#define TOTAL_FOB_SIZE      N_FOB*FOB_SCI_DATA_SIZE 
#define TOTAL_FSC_SIZE      N_FSC*FSC_SCI_DATA_SIZE
#define TOTAL_PC_PCKT_SIZE  TOTAL_FIB_SIZE + TOTAL_FOB_SIZE + TOTAL_FSC_SIZE  + 8
#pragma pack(1)                                                 /*eliminates byte padding*/
union pc_data
{
  struct
  {
    byte id; 
    unsigned long time1; 
    byte n_fib; 
    byte n_fob; 
    byte n_fsc; 
    byte sci_fib[TOTAL_FIB_SIZE]; 
    byte sci_fob[TOTAL_FOB_SIZE]; 
    byte sci_fsc[TOTAL_FSC_SIZE]; 
  };
  byte arr[8+TOTAL_FIB_SIZE+TOTAL_FOB_SIZE+TOTAL_FSC_SIZE]; 
};

#endif
