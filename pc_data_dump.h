#ifndef PC_DATA_DUMP_H
#define PC_DATA_DUMP_H

#define FIB_SCI_DATA_SIZE   10
#define FOB_SCI_DATA_SIZE   10
#define FSC_SCI_DATA_SIZE   10
#define N_FIB               0 
#define N_FOB               0
#define N_FSC               1
#define TOTAL_FIB_SIZE      N_FIB*FIB_SCI_DATA_SIZE
#define TOTAL_FOB_SIZE      N_FOB*FOB_SCI_DATA_SIZE 
#define TOTAL_FSC_SIZE      N_FSC*FSC_SCI_DATA_SIZE
#define TOTAL_PC_PCKT_SIZE  TOTAL_FIB_SIZE + TOTAL_FOB_SIZE + TOTAL_FSC_SIZE  + 8; 
union pc_data
{
  struct
  {
    uint8_t id;
    unsigned time1;
    uint8_t n_fib; 
    uint8_t n_fob; 
    uint8_t n_fsc;
    uint8_t sci_fib[TOTAL_FIB_SIZE];
    uint8_t sci_fob[TOTAL_FOB_SIZE];
    uint8_t sci_fsc[TOTAL_FSC_SIZE];  
  };
  uint8_t pc_pckt[8+TOTAL_FIB_SIZE+TOTAL_FOB_SIZE+TOTAL_FSC_SIZE]; 
};

#endif

