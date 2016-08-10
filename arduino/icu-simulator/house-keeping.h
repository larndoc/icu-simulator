

#pragma pack (1)


union house_keeping
{
struct

{
	byte status; 
	unsigned long time; 
	byte pcu_data[2][16]; 
	byte fib; 
	byte fob; 
	byte fsc;
};
	byte arr[1 + 4 + 32 + 3];

};
