#ifndef _ICU-SIMULATOR-PINS_h
#define _ICU-SIMULATOR-PINS_h


#define FIB_SYNC			7
#define FOB_SYNC			6 
#define FSC_SYNC			5 

#define UART_D        2
#define UART_S        3

#define UART_FIB_D			&Serial1 
#define UART_FOB_D			&Serial2 
#define UART_FSC_D 			&Serial3
 
#define UART_FIB_S      &Serial3 
#define UART_FOB_S      &Serial1 
#define UART_FSC_S      &Serial2 

#define CS1_PIN		        38 
#define CS0_PIN 		      40 
#define EN_FIB	41 
#define EN_FOB	43
#define EN_FSC	42
#define CG_FIB	30 
#define CG_FOB	33 
#define CG_FSC	32 
#define CG_ICU	35 
#define ALIVE_PIN 	39
#define DEBUG_PIN     10



#endif
