#define FIB_SCI_DATA_SIZE		10
#define FOB_SCI_DATA_SIZE		10
#define	FSC_SCI_DATA_SIZE		10


union pc_data
[
	struct
	{
		uint8_t		id
		unsigned 	time;
		uint8_t		n-fib; 
		uint8_t		n-fob; 
		uint8_t		n-fsc;
		uint8_t 	sci-fib[n-fib*FIB_SCI_DATA_SIZE];
		uint8_t		sci-fob[n-fob*FOB_SCI_DATA_SIZE];
		uint8_t		sci-fsc[n-fsc*FSC_SCI_DATA_SIZE];	
	};
	uint8_t pc_pckt[8 + n-fib*FIB_SCI_DATA_SIZE + n-fob*FOB_SCIE_DATA_SIZE + n-fsc*FSC_SCI_DATA_SIZE]; 

]