#ifndef _adc_h
#define _adc_h

#define NUM_ADCS 2
#define ADC_VSENSE 0
#define ADC_ISENSE 1

#define ADC_VSENSE_CS 41
#define ADC_ISENSE_CS 38

extern uint16_t adc_readings[NUM_ADCS][8];
extern void adc_read_one(uint8_t chip, uint8_t pin);
extern void adc_read_all(uint8_t chip);

#endif /* !defined _adc_h */
