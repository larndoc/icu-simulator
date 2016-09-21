/* options and configuration */
#ifndef _opts_h
#define _opts_h

#define FIB_SCI 0
#define FOB_SCI 1
#define FSC_SCI 2
#define FIB_HK  3
#define FOB_HK  4
#define FSC_HK  5
#define PCU_HK  6
#define N_DEV   7

struct _opts {
	char *wf[N_DEV];
	bool enabled[N_DEV];
	double freq[N_DEV],
	       T; /* time between samples in seconds */
	bool verbose;
	char min_priority, *dir_out;
	long n, noise_ampl;
	long dp_per_output; /* number of samples to buffer */
};

/* default noise amplitude: can enable without specifying */
#define DEFAULT_NOISE_AMPL 512
/* amplitude for sine(), square(), random(), etc */
#define DEFAULT_AMPLITUDE 2048
/* US_JITTER can set time off-base */
#define US_JITTER 1

/* makes calling localtime() prettier */
#define _local_time() (&(time_t){time(NULL)})

/* number of data points to generate by device */
const int num_dp[N_DEV] = {4, 4, 6, 25, 1, 27, 16};

const char interfaces[N_DEV][8] = { "fib_sci",
				    "fob_sci",
				    "fsc_sci",
				    "fib_hk" ,
				    "fob_hk" ,
				    "fsc_hk" ,
				    "pcu_hk" };
/* filename format strings by device*/
const char names[N_DEV][64] = {"FIB_Sci_TM_%04d%02d%02d_%02d%02d%02d.csv",
			       "FOB_Sci_TM_%04d%02d%02d_%02d%02d%02d.csv",
			       "FSC_Sci_TM_%04d%02d%02d_%02d%02d%02d.csv",
			       "FIB_HK_TM_%04d%02d%02d_%02d%02d%02d.csv" ,
			       "FOB_HK_TM_%04d%02d%02d_%02d%02d%02d.csv" ,
			       "FSC_HK_TM_%04d%02d%02d_%02d%02d%02d.csv" ,
			       "PCU_HK_TM_%04d%02d%02d_%02d%02d%02d.csv" };

/* CSV header strings by device */
const char headers[N_DEV][512] = {
		/* FIB SCI */
		"Time,Bx,By,Bz,Status",
		/* FOB SCI */
		"Time,Bx,By,Bz,Range",
		/* FSC SCI */
		"Time,Sensor_Laser,Laser_Micro,Zeeman,Sci_Data_ID,Sci_Data,"
			"Timestamp",
		/* FIB HK */
		"Time,Status_HB,Status_LB,LUP_cnt,P1V5,P3V3,P5V,N5V,P8V,P12V,"
			"P1I5,P3I3,P5I,N5I,P8I,P12I,TE,TS1,TS2,Checksum,"
			"CMD_exec_cnt,ICU_err_cnt,Last_cmd,Last_err,HK_req_cnt,"
			"sync_count",
		/* FOB HK */
		"Time,FOB",
		/* FSC HK */
		"Time,Peregrine_Lock,Sensor_Temp_A,Sensor_Temp_B,"
			"Sensor_Temp_Duty_Cycle,Laser_Temp_A,Laser_Temp_B,"
			"Laser_Temp_Duty_Cycle,Laser_Current,"
			"Laser_Current_Zero_Cross,Microwave_Ref,"
			"Microwave_Ref_Zero_Cross,Zeeman_Freq_Zero_Cross,"
			"PCB_Temp_A,PCB_Temp_B,Laser_Diode_Voltage,"
			"Diode_Optical_Power,P2V4,P3V3,P8V,N8V,P12V,PCB_Temp_C,"
			"PCB_Temp_D,PCB_Temp_E,ICU_Checksum,ICU_Command_Count,"
			"ICU_Sync_Count",
		/* PCU HK */
		"Time,I_FIB,I_FOB,I_FSC,I_P3V3,I_FIBH,I_FOBH,I_FSCH,I_P1V8,"
			"Temp,V_P2V4,V_P3V3,V_P12V,V_P8V,V_N8V,V_P5V,V_N5V"
};

extern struct _opts opts;
#endif /* !defined _opts_h */
