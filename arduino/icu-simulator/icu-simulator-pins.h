#ifndef _ICU-SIMULATOR-PINS_h
#define _ICU-SIMULATOR-PINS_h


#define FIB_SYNC			7
#define FOB_SYNC			6 
#define FSC_SYNC			5 

#define UART_D        2
#define UART_S        3

#define FIB_RX_D        19
#define FIB_TX_D        18
#define FOB_RX_D        17
#define FOB_TX_D        16
#define FSC_RX_D        15
#define FSC_TX_D        14

#define UART_FIB_D			&Serial1 
#define UART_FOB_D			&Serial2 
#define UART_FSC_D 			&Serial3

#define FIB_RX_S        15
#define FIB_TX_S        14
#define FOB_RX_S        19
#define FOB_TX_S        18
#define FSC_RX_S        17
#define FSC_TX_S        16
 
#define UART_FIB_S      &Serial3 
#define UART_FOB_S      &Serial1 
#define UART_FSC_S      &Serial2 

#define CS1_PIN		      38 
#define CS0_PIN 		    40 
#define EN_FIB	        41 
#define EN_FOB	        42
#define EN_FSC	        43
#define CG_FIB	        30 
#define CG_FOB	        33 
#define CG_FSC	        32 
#define CG_ICU	        35 
#define ALIVE_PIN 	    39
#define DEBUG_PIN       13



#endif
