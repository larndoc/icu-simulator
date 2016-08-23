#ifndef PC_DATA_DUMP_H
#define PC_DATA_DUMP_H
#pragma pack(1)  

                                               /*eliminates byte padding*/
union pc_data
{
  struct
  {
    byte id; 
    signed long sync_counter; 
    byte n_fib; 
    byte n_fob; 
    byte n_fsc; 
  };
  byte arr[8]; 
};

#endif
