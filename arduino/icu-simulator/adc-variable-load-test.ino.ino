#include <SPI.h>
#include <errno.h>

#define NUM_ADCS 2
#define ADC_VSENSE 0
#define ADC_ISENSE 1

#define LOAD_VDD_IO  0
#define LOAD_VDD_CORE 1

#define I_MIN 0.0f
#define I_MAX 1.0f

uint16_t adc_readings[NUM_ADCS][8];

__attribute__((flatten))
int adc_get_chip_select(int adc)
{
  switch (adc) {
    case ADC_VSENSE:
      return 41;
    case ADC_ISENSE:
      return 38;
    default:
      return -EINVAL;
  } 
}

void adc_read_one(unsigned char chip, unsigned char pin)
{
  int16_t result, chip_select = adc_get_chip_select(chip);
  if (chip_select < 0) return;
  
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
    digitalWrite(chip_select, LOW);
    SPI.transfer16(pin << 11);
    result = SPI.transfer16(pin << 11);
    adc_readings[chip][pin] = result;
    digitalWrite(chip_select, HIGH);
  SPI.endTransaction();
  
  adc_readings[chip][pin] = result;
}

void adc_read_all(unsigned char chip)
{
  int16_t result, chip_select = adc_get_chip_select(chip);
  if (chip_select < 0) {
    Serial.println("chip_select < 0");
    return;
  }

  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
    digitalWrite(chip_select, LOW);
    SPI.transfer16(0); /* ignore the last result */
    for (int i = 0; i < 8; i++) 
        adc_readings[chip][i] = SPI.transfer16((i+1) << 11);
    digitalWrite(chip_select, HIGH);
  SPI.endTransaction();
}

void set_load(unsigned char rail, float current)
{
  //analogWriteResolution(12);
  float dac_out_flt = 4096 * current / (I_MIN - I_MAX) + 4095;
  // no negatives
  dac_out_flt = (dac_out_flt < 0.0f ? -dac_out_flt : dac_out_flt);
  // convert to uint16_t and clamp to interval [0, 4095].
  uint16_t dac_out = (uint16_t) dac_out_flt;
  dac_out = (dac_out > 4095 ? 4095 : dac_out);
  
  analogWrite(66 + rail, dac_out);  
}



void setup() {
  Serial.begin(9600);

  // start the SPI library:
  SPI.begin();

  // initalize the  data ready and chip select pins:
  pinMode(41, OUTPUT);
  set_load(LOAD_VDD_IO,   0.2);
  set_load(LOAD_VDD_CORE, 0.2);

}

void loop() {
  Serial.print("Requesting all readings... ");
  adc_read_all(ADC_VSENSE);
  Serial.print(adc_readings[ADC_VSENSE][0]);
  Serial.print("\t");
  Serial.println(adc_readings[ADC_VSENSE][4]);
  delay(50);
}
