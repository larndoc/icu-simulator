#ifndef PC_DATA_DUMP_H
#define PC_DATA_DUMP_H
#pragma pack(1)  

                                               /*eliminates byte padding*/
union pc_data
{
  struct
  {
    byte id; 
    uint32_t sync_counter; 
  };
  byte arr[5]; 
};

#endif
