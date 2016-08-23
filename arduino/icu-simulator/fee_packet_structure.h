#ifndef FEE_PACKET_STRUCTURE_H
#define FEE_PACKET_STRUCTURE_H
#define FEE_PACKET_HEADER_SIZE 	  	  1
#define FSC_SCI_DATA_LENGTH		  11
#define FIB_SCI_DATA_LENGTH               10 
#define FOB_SCI_DATA_LENGTH               10 
#define FIB_HOUSE_KEEPING_DATA_LENGTH     40 
#define FOB_HOUSE_KEEPING_DATA_LENGTH     4
#define FSC_HOUSE_KEEPING_DATA_LENGTH     53
#define	CONFIG_PARAM_ID 		  1
#define	CONFIG_PARAM_VAL	          1 
#define CHECKSUM_VAL		          1 	
#define FIB_TOTAL_LENGTH                  FEE_PACKET_HEADER_SIZE + FIB_SCI_DATA_LENGTH + CONFIG_PARAM_ID + CONFIG_PARAM_VAL + CHECKSUM_VAL  + FIB_HOUSE_KEEPING_DATA_LENGTH
#define FOB_TOTAL_LENGTH                  FEE_PACKET_HEADER_SIZE + FOB_SCI_DATA_LENGTH + CONFIG_PARAM_ID + CONFIG_PARAM_VAL + CHECKSUM_VAL  + FOB_HOUSE_KEEPING_DATA_LENGTH 
#define FSC_TOTAL_LENGTH                  FEE_PACKET_HEADER_SIZE + FSC_SCI_DATA_LENGTH + CONFIG_PARAM_ID + CONFIG_PARAM_VAL + CHECKSUM_VAL  + FSC_HOUSE_KEEPING_DATA_LENGTH

#pragma pack(1)       /*eliminates byte padding */
union fib_paket
{
	struct
	{
		byte header; 
		byte science_data[FIB_SCI_DATA_LENGTH];
                byte hk_data[FIB_HOUSE_KEEPING_DATA_LENGTH];
		byte config_param_id[CONFIG_PARAM_ID]; 
		byte config_param_val[CONFIG_PARAM_VAL];
		byte checksum[CHECKSUM_VAL];
	};
	byte arr[FIB_SCI_DATA_LENGTH];
};

union fsc_packet
{
  struct
  {
    byte header; 
    byte science_data[FSC_SCI_DATA_LENGTH ]; 
    byte hk_data[FSC_HOUSE_KEEPING_DATA_LENGTH];
    byte config_param_id[CONFIG_PARAM_ID]; 
    byte config_param_val[CONFIG_PARAM_VAL]; 
    byte checksum[CHECKSUM_VAL]; 
  };
  byte arr[FSC_TOTAL_LENGTH]; 
};

union fob_packet 
{
  struct 
  {
    byte header; 
    byte science_data[FOB_SCI_DATA_LENGTH];  
    byte hk_data[FOB_HOUSE_KEEPING_DATA_LENGTH];
    byte config_param_id[CONFIG_PARAM_ID]; 
    byte config_param_val[CONFIG_PARAM_VAL]; 
    byte checksum[CHECKSUM_VAL]; 
  };
  byte arr[FOB_TOTAL_LENGTH];
  }; 

#endif
