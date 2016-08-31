/* Lab model of ICU: PCU ADC */
#include <SPI.h>
#include <errno.h>
#include "adc.h"

inline
int16_t adc_get_chip_select(int16_t adc)
{
	switch (adc) {
		case ADC_VSENSE:
			return ADC_VSENSE_CS;
		case ADC_ISENSE:
			return ADC_ISENSE_CS;
		default:
			return -EINVAL;
	}	
}

void adc_read_one(uint8_t chip, uint8_t pin)
{
	int16_t result, chip_select = adc_get_chip_select(chip);
	if (chip_select < 0) return;

	SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
	digitalWrite(chip_select, LOW);

	  SPI.transfer16(pin << 11);
	  result = SPI.transfer16(pin << 11);
	  result &= 0x0FFF;
	  adc_readings[chip][pin] = result;
	
	digitalWrite(chip_select, HIGH);
	SPI.endTransaction();
	
	adc_readings[chip][pin] = result;
}

void adc_read_all(uint8_t chip)
{
	int16_t result, chip_select = adc_get_chip_select(chip);
	if (chip_select < 0) return;

	SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
	digitalWrite(chip_select, LOW);
	
	  SPI.transfer16(0); /* ignore the last result */
	  for (int i = 0; i < 8; i++) 
	  	  adc_readings[chip][i] = SPI.transfer16((i+1) << 11) & 0x0FFF;
	
	digitalWrite(chip_select, HIGH);
	SPI.endTransaction();
}
