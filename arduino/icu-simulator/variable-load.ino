/* Lab model of ICU: set varaible load.*/ 
#define LOAD_VDD_IO	0
#define LOAD_VDD_CORE	1

#define I_MIN 0.0f
#define I_MAX 1.0f

void set_load(uint8_t rail, float current)
{
	analogWriteResolution(12);
	float dac_out_flt = 4096 * current / (I_MIN - I_MAX) + 4095;
	// no negatives
	dac_out_flt = (dac_out_flt < 0.0f ? -dac_out_flt : dac_out_flt);
	
	// convert to uint16_t and clamp to interval [0, 4095].
	uint16_t dac_out = (uint16_t) dac_out_flt;
	dac_out = (dac_out > 4095 ? 4095 : dac_out);
	
	analogWrite(66 + rail, dac_out);	
}
