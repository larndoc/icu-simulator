#ifndef PC_DATA_DUMP_H
#define PC_DATA_DUMP_H
#pragma pack(1)  

                                               /*eliminates byte padding*/
union pc_data
{
  struct
  {
    byte id; 
    unsigned long time1; 
    byte n_fib; 
    byte n_fob; 
    byte n_fsc; 
    byte sci_fib[10]; 
    byte sci_fob[10]; 
    byte sci_fsc[10]; 
  };
  byte arr[38]; 
};

#endif
