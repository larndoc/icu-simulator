#define FEE_PACKET_HEADER_OFFSET 	0 
#define FEE_PACKET_SIZE 			100 
#define FEE_PACKET_HEADER_SIZE 		1 
#define SCIENCE_DATA_LENGTH			10 
#define HOUSE_KEEPING_DATA			5
#define	CONFIG_PARAM_ID 			1
#define	CONFIG_PARAM_VAL			1
#define CHECKSUM_SIZE				100
#define CHECKSUM_VAL				1	
union fee_paket
{
	struct
	{
		uint8_t header; 
		uint8_t science_data[SCIENCE_DATA_LENGTH]; 
		uint8_t hk_data[HOUSE_KEEPING_DATA];
		uint8_t config_param_id[CONFIG_PARAM_ID]; 
		uint8_t config_param_val[CONFIG_PARAM_VAL];
		uint8_t checksum[CHECKSUM_VAL];
	};
	uint8_t arr[FEE_PACKET_SIZE];
};