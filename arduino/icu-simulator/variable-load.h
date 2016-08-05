#ifndef _variable_load_h
#define _variable_load_h
#define LOAD_VDD_IO	0
#define LOAD_VDD_CORE	1

#define I_MIN 0.0f
#define I_MAX 1.0f

extern void set_load(uint8_t rail, float current);

#endif // !defined _variable_load_h
