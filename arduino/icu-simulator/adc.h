#ifndef _adc_h
#define _adc_h

#define NUM_ADCS 2
#define ADC_VSENSE 0
#define ADC_ISENSE 1

#define ADC_VSENSE_CS 40
#define ADC_ISENSE_CS 38

uint16_t adc_readings[NUM_ADCS][8];
void adc_read_one(uint8_t chip, uint8_t pin);
void adc_read_all(uint8_t chip);

#endif /* !defined _adc_h */
