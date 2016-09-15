#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <tgmath.h>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdarg.h>
#include <errno.h>
#include <limits.h>
/* FIXME: square wave generator is broken;
 * returns 1024 for 10 or so points, then
 * 0 for only two (duty cycle > 50%).
 */

/* FIXME: find a GENSYM macro that works */
#define ARGV_COUNTER _argv_counter
#define PREV_ARG ARGV_COUNTER--
#define NEXT_ARG ARGV_COUNTER++
#define THIS_ARG argv[ARGV_COUNTER]
#define NEXT_ARG_MUST_EXIST do { NEXT_ARG; CHECK_ARGV; } while (0)
#define LOOP_ARGV for (int ARGV_COUNTER = 1; ARGV_COUNTER < argc; NEXT_ARG)
#define IF_ARG(x) if (!strcasecmp(argv[ARGV_COUNTER], x))
#define IF_NOT_ARG(x) if (strcasecmp(argv[ARGV_COUNTER], x))
#define IF_ARG_EXISTS if (ARGV_COUNTER < argc)
#define IF_ARG_NOT_EXISTS if (ARGV_COUNTER >= argc)
#define CHECK_ARGV if (ARGV_COUNTER >= argc) usage(argv[0], "CHECK_ARGV")
#define PARSE_WAVE(wf,f) do{debug(D_INFO,				      \
				  "Incrementing argument counter...\n");      \
			    ARGV_COUNTER++; CHECK_ARGV;			      \
			    IF_ARG("sine"){debug(D_BUG_RESOLVED,"Got sine\n");\
			    	    wf = sine;}		                      \
			    else IF_ARG("square"){debug(D_BUG_RESOLVED,       \
			    			  "Got square\n");            \
			    	    		   wf = square;}	      \
			    else IF_ARG("sawtooth"){debug(D_BUG_RESOLVED,     \
						      "Got sawtooth\n");      \
						wf = sawtooth;}		      \
			    else IF_ARG("random"){debug(D_BUG_RESOLVED,       \
			    				"Got random\n");      \
					      wf = _random;}	              \
			    else usage(argv[0], "PARSE_WAVE");		      \
			IF_NOT_ARG("random") {			              \
			ARGV_COUNTER++; CHECK_ARGV;		              \
			f=atof(argv[ARGV_COUNTER]);		              \
			debug(D_INFO, "parsed freq %f\n", f);}} while (0)
#define ENSURE_WF_EXISTS(d) if(opts.enabled[d]&&!opts.wf[d])opts.wf[d]=_random

#define unpack_time(tv,mod) ((double)tv.tv_sec + 1e-6*(double)tv.tv_usec)

#define FIB_SCI 0
#define FOB_SCI 1
#define FSC_SCI 2
#define FIB_HK  3
#define FOB_HK  4
#define FSC_HK  5
#define PCU_HK  6
#define N_DEV   7

/* ASCII escape codes for nice terminal printing */
#define FG_RED		"\033[31m"
#define FG_YELLOW	"\033[33m"
#define FG_BLUE		"\033[34m"
#define FG_PURPLE	"\033[35m"
#define TEXT_BOLD 	"\033[1m"
#define COLOR_END	"\033[0m"


#define fmt_from_tm(tm) tm->tm_year,tm->tm_mon,tm->tm_mday,\
			tm->tm_hour,tm->tm_min,tm->tm_sec

/* pretty-printing debugging stuff */
void _debug(int, char *, const char *, char *, int, char *, ...);
#define debug(level, ...) _debug(level, __FILE__, __func__, NULL, __LINE__,\
				 __VA_ARGS__);

const char *log_tags[ ] = { FG_BLUE   "[+] " COLOR_END,  /* INFO */
			    FG_PURPLE "[-] " COLOR_END,  /* BUG RESOLVED */
			    FG_YELLOW "[*] " COLOR_END,  /* NOTICE */
		     TEXT_BOLD FG_RED "[!] " COLOR_END}; /* BUG UNRESOLVED */

/* Use D_INFO to trace program flow,
 * D_BUG_UNRESOLVED to flag debug
 * statements relating to unresolved bugs (hurr)
 * D_BUG_RESOLVED when the bug is resolved
 * (bugs are fixed with hacky code, which
 * is often just as breakable - we wanna
 * debug the fixes), and D_NOTICE to
 * call attention to wonky behavior
 * or communicate critical info with the user.
 * (remember D_INFO is usually turned off)
 */
#define D_INFO 0
#define D_NOTICE 2
#define D_BUG_RESOLVED 1
#define D_BUG_UNRESOLVED 3

/* default noise amplitude: can enable without specifying */
#define DEFAULT_NOISE_AMPL 512
/* amplitude for sine(), square(), random(), etc */
#define DEFAULT_AMPLITUDE 4096

/* makes calling localtime() prettier */
#define _local_time() (&(time_t){time(NULL)})

// make -Wall stfu
#ifdef __GNUC__
#define _unused __attribute__((unused))
#else
#define _unused
#endif

bool parse_long(char *str, long *ret)
{
	char *check;
	long _ret = strtol(str, &check, 10);
	if (((_ret == LONG_MAX || _ret == LONG_MIN) && errno == ERANGE)
	                                          || (check == str)) {
		debug(D_NOTICE, TEXT_BOLD FG_RED
				"Warning: expected integer, got string \"%s\""
				COLOR_END "\nProceeding with ret=0",
				str);
		return false;
	}

	*ret = _ret;
	return true;
}

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

/* number of data points to generate by device */
const int num_dp[N_DEV] = {4, 4, 6, 25, 1, 27, 16};

/* data generator function prototype */
typedef int (*data_generator_func_t)(int, double);

/* global options structure */
struct {
	bool enabled[N_DEV];
	data_generator_func_t wf[N_DEV];
	double freq[N_DEV],
	       T; /* time between samples in seconds */
	bool verbose;
	char min_priority, *dir_out;
	long n, noise_ampl;
	long dp_per_output; /* number of samples to buffer */
} opts;

struct timestamp {
	long y,
	     mo,
	     d,
	     h,
	     mi, /* minute      */
	     s,  /* second      */
	     us; /* microsecond */
} tzero, now;

#define is_leap_year(x) ((x%400) || (!(x%4) && (x%100)))
#define wrap(var, lim, of) if (var < lim); else { var = fmod(var, lim); of++; }
void tick()
{
	now.us += 1e6 * opts.T;
	wrap(now.us, 1000000, now.s);
	wrap(now.s, 60, now.mi);
	wrap(now.mi, 60, now.h);
	wrap(now.h, 24, now.d);
	switch (now.mo) {
		case 1:
		case 3:
		case 5:
		case 7:
		case 8:
		case 10:
		case 12:
			wrap(now.d, 31, now.mo);
			break;
		case 2:
			if (is_leap_year(now.y)) {
				wrap(now.d, 29, now.mo);
			} else {
				wrap(now.d, 28, now.mo);
			}
			break;
		default:
			wrap(now.d, 30, now.mo);
	}
	wrap(now.mo, 12, now.y);
}

void timestamp(FILE *f)
{
	fprintf(f, "%04ld-%02ld-%02ldT%02ld:%02ld:%02ld.%06ld,",
		now.y, now.mo, now.d, now.h, now.mi,
		now.s, now.us);
}

#define clk() _ts_to_s(now)
double _ts_to_s(struct timestamp ts) {
	return ts.h  / 3600.0
	     + ts.mi /   60.0
	     + (double) ts.s
	     + ts.us * 1e6;
}

int sine(int A, double f)
{
	double t = clk();
	int ret = A * sin(2*M_PI*f*t);

	if (opts.noise_ampl)
		ret += random() % opts.noise_ampl;

	return ret;
}

int square(int A, double f)
{
	// I ASSURE YOU THIS SOMETIMES WORKS
	double y = sine(1, f);
	int ret = y > 0 ? A
			: (fabs(y) < 1.0f ? A/2
					  : 0);
	if (opts.noise_ampl)
		ret += random() % opts.noise_ampl;

	return ret;
}

int sawtooth(int A, double f)
{
	// THIS? ALMOST NEVER
	double t = clk();
	double T = 1/f;
	t  = fmodf(t, T);
	int ret = A * ((f*t) - floor(f*t));

	if (opts.noise_ampl)
		ret += random() % opts.noise_ampl;

	return ret;
}

int _random(int A _unused, double f _unused)
{
	// durrrrr
	return random() % A;
}

char *prepare_path(char *path, char *fname)
{
	size_t to_alloc = strlen(path) + strlen(fname) + 2;
	char *ret = malloc(to_alloc);
	for (int i = 0; i < to_alloc; i++)
		ret[i] = 0;
	strcat(ret, path);
	if (path[strlen(path)-1] != '/')
		strcat(ret, "/");
	strcat(ret, fname);
	debug(D_BUG_UNRESOLVED, "Prepared path: %s\nat <0x%x>", ret, (unsigned long long) ret);
	return ret;
}

#define usage(name, reason) _usage(__FILE__, __LINE__, __func__, name, reason)
void _usage(char *file, int line, const char *func, const char *name, const char *reason)
{
	printf( "%s: fake data streams for all your testing needs.\n"
		"Problems? Contact me: <he915@ic.ac.uk>.\n"
		"All parts can be referenced as {part}{_hk,_sci,}\n"
		"Options:\n"
		"\tfib		Produce fake FIB data\n"
		"\tfob		Produce fake FOB data\n"
		"\tfsc		Produce fake FSC data\n"
		"\tpcu		Produce fake PCU data\n"
		"\tw		Specify waveform to produce for target device\n"
		"\twaveform	\"\n"
		"\t             Usage: wave [part] [wave_type] [freq]\n"
		"\t             Where [part] in {fib, fob, fsc, pcu},\n"
		"\t                   [wave_type] in {square, sine, sawtooth,"
								   "random}\n"
		"\t                   [freq] is a double; don't supply to"
						      "random waveforms\n"
		"\tf		\n"
		"\tfile         Specify file output path\n"
		"\t             Usage: file [path]\n"
		"\t             Where [path] is a path to desired output"
							       "folder\n"
		"\tT		\n"
		"\ttime         Time to wait after each new data point\"\n"
		"\t             Usage: time [time]\n"
		"\t             Where [time] is of the form [double][unit];\n"
		"\t                 [double] is a doubleing-point number;\n"
		"\t                 [unit]  is blank for time in seconds,\n"
		"\t                         or one of {us,ms,s}.\n"
		"\tf            \n"
		"\tfreq         Frequency at which to produce new data points."
		"\t             Usage: freq [double][unit],\n"
		"\t             Where [unit] is one of [mHz, Hz, kHz]\n"
		"\t             Note that time and freq options supercede each"
								     "other;\n"
		"\t                 this program will only use the value"
		                                           "calculated\n"
		"\t                 from the last option specified on the"
			 				  "command line\n"
		"\tn\n"
		"\tnumber       Number of data points to print.\n"
		"\t             Usage: number [nr]\n"
		"\t             Where [nr] is an integer\n"
		"\tnper\n"
		"\tnbuf\n"
		"\tbuf\n"
		"\tbuffer       Number of data points to buffer before output\n"
		"\t             (i.e. will output nper * f points per second)\n"
		"Example usage:\n"
		"\t%s fib fob pcu wave fib square 10 wave fob sine 25 t 250ms\n"
		"\t%s fib_hk fsc_sci wave fib_hk random\n"
		"\t%s fob_hk freq 128 Hz wf fob_hk sine 0.5 noise\n"
		"--------------------------------------------------------\n"
		"If you're seeing this, something probably went wrong.\n"
		"If so, the error was here: %s:%d, in a call to %s().\n"
		"Here's the reason we were called: %s\n",
		name, name, name, name, file, line, func, reason);
	exit(1);
}


int main(int argc, char *argv[])
{
	char s[2];
	FILE *out[N_DEV];
	char fnames[N_DEV][64];

	srandom(time(NULL));
	
	struct tm tm_zero = *localtime(_local_time());
	tm_zero.tm_year += 1900;
	tm_zero.tm_mon++;

	tzero.y  = tm_zero.tm_year;
	tzero.mo = tm_zero.tm_mon;
	tzero.d  = tm_zero.tm_mday;
	tzero.h  = tm_zero.tm_hour;
	tzero.mi = tm_zero.tm_min;
	tzero.s  = tm_zero.tm_sec;
	tzero.us = 0;
	now = tzero;

	debug(D_BUG_UNRESOLVED, "timestamping stdout...");
	timestamp(stdout); printf("\n");
	debug(D_BUG_UNRESOLVED, "wtf?");


	debug(D_INFO, "This is\ntesting the\nlogging facility.");

	debug(D_INFO, "Setting default opts...\n");
	opts.T = 0.1f;
	opts.dir_out = "/data/";
	opts.n = 0;
	opts.dp_per_output = 1;
	opts.noise_ampl = 0;
	for (int j = 0; j < N_DEV; j++) {
		opts.enabled[j] = false;
		opts.wf[j] 	= NULL;
		opts.freq[j]    = 0.0f;
	}

	/* don't be so deluded as to believe that proper
	 * justification for what I am doing here today exists.
	 */
	debug(D_INFO, "Entering LOOP_ARGV; argc=%d\n", argc);
	LOOP_ARGV {
		debug(D_INFO, "Parsing args with ARGV_COUNTER=%d\n",
		      ARGV_COUNTER);
		/* these opts enable entire interfaces */
		IF_ARG("fib") {
			debug(D_INFO, "Enabling fib...\n");
			opts.enabled[FIB_SCI] = true;
			opts.enabled[FIB_HK]  = true;
		} else IF_ARG("fob") {
			debug(D_INFO, "Enabling fob...\n");
			opts.enabled[FOB_SCI] = true;
			opts.enabled[FOB_HK]  = true;
		} else IF_ARG("fsc") {
			opts.enabled[FSC_SCI] = true;
			opts.enabled[FSC_HK]  = true;
		} else IF_ARG("pcu")
			opts.enabled[PCU_HK]  = true;

		/* these handle specific modules */
		else IF_ARG("fib_sci") opts.enabled[FIB_SCI] = true;
		else IF_ARG("fob_sci") opts.enabled[FOB_SCI] = true;
		else IF_ARG("fsc_sci") opts.enabled[FSC_SCI] = true;
		else IF_ARG("fib_hk")  opts.enabled[FIB_HK]  = true;
		else IF_ARG("fob_hk")  opts.enabled[FOB_HK]  = true;
		else IF_ARG("fsc_hk")  opts.enabled[FSC_HK]  = true;
		else IF_ARG("pcu_hk")  opts.enabled[PCU_HK]  = true;

		/* enable verbose output */
		else IF_ARG("verbose")	opts.verbose = true;
		else IF_ARG("v")	opts.verbose = true;

		/* set number of data points */
		else IF_ARG("n") {
			NEXT_ARG_MUST_EXIST;
			if (!parse_long(THIS_ARG, &opts.n)) {
				debug(D_NOTICE, "Ignoring data point cap...\n");
				opts.n = 0;
			}
		}

		/* user wants a particular waveform */
		else IF_ARG("w")    goto waveform;
		else IF_ARG("wf")   goto waveform;
		else IF_ARG("wave") goto waveform;
		else IF_ARG("waveform") {
			waveform:
			debug(D_INFO, "Got waveform; parsing...\n");
			NEXT_ARG_MUST_EXIST;
			/* to be totally clear, this trick relies on the RHS *
			 * of assignment evaluating before the LHS, and	     *
			 * assignment evaluating to the RHS value. After the *
			 * assignment a = b = c, (a==c) && (b==c) => true.   */
			IF_ARG("fib")
				PARSE_WAVE(opts.wf[FIB_SCI]
					   = opts.wf[FIB_HK],
					   opts.freq[FIB_SCI]
					   = opts.freq[FIB_HK]);
			else IF_ARG("fob")
				PARSE_WAVE(opts.wf[FOB_SCI]
					   = opts.wf[FOB_HK],
					   opts.freq[FOB_SCI]
					   = opts.freq[FOB_HK]);
			else IF_ARG("fsc")
				PARSE_WAVE(opts.wf[FSC_SCI]
					   = opts.wf[FSC_HK],
					   opts.freq[FSC_SCI]
					   = opts.freq[FSC_HK]);

			else IF_ARG("fib_sci") PARSE_WAVE(opts.wf[FIB_SCI],
							  opts.freq[FIB_SCI]);
			else IF_ARG("fob_sci") PARSE_WAVE(opts.wf[FOB_SCI],
							  opts.freq[FOB_SCI]);
			else IF_ARG("fsc_sci") PARSE_WAVE(opts.wf[FSC_SCI],
							  opts.freq[FSC_SCI]);
			else IF_ARG("fib_hk")  PARSE_WAVE(opts.wf[FIB_HK],
							  opts.freq[FIB_HK]);
			else IF_ARG("fob_hk")  PARSE_WAVE(opts.wf[FOB_HK],
							  opts.freq[FOB_HK]);
			else IF_ARG("fsc_hk")  PARSE_WAVE(opts.wf[FSC_HK],
							  opts.freq[FSC_HK]);
			else IF_ARG("pcu")     PARSE_WAVE(opts.wf[PCU_HK],
							  opts.freq[PCU_HK]);
			else usage(argv[0], "invalid waveform specified");
		}

		/* inject noise into the signal optionally */
		else IF_ARG("no")   goto noise;
		else IF_ARG("noi")  goto noise;
		else IF_ARG("nois") goto noise;
		else IF_ARG("noise") {
			noise:
			NEXT_ARG;
			IF_ARG_EXISTS {
				if (!parse_long(THIS_ARG, &opts.noise_ampl)) {
					debug(D_NOTICE,
					      "Continuing with noise amplitude"
					      " %d\n", DEFAULT_NOISE_AMPL);
					opts.noise_ampl = DEFAULT_NOISE_AMPL;
					PREV_ARG;
				}
			} else {
				PREV_ARG;
				opts.noise_ampl = DEFAULT_NOISE_AMPL;
			}

		}

		/* specify file output path (default: /data/) */
		else IF_ARG("fi") goto file;
		else IF_ARG("fil") goto file;
		else IF_ARG("file") {
			file:
			NEXT_ARG_MUST_EXIST;
			opts.dir_out = THIS_ARG;
			debug(D_INFO, "filepath: got %s\n", opts.dir_out);
		}

		/* specify time to wait between new data points *
		 * (default: 100ms) 				*/
		else IF_ARG("t") goto time;
		else IF_ARG("time") {
			time:
			debug(D_BUG_RESOLVED, "Parsing time argument...");
			NEXT_ARG_MUST_EXIST;
			sscanf(THIS_ARG, "%lf%2s", &opts.T, s);
			debug(D_INFO, "Time: got %lf ", opts.T);
			switch (s[0]) {
			case 'u':
				debug(D_BUG_RESOLVED, "us\n");
				opts.T *= 1e-6;
				break;
			case 'm':
				debug(D_BUG_RESOLVED, "ms\n");
				opts.T *= 1e-3;
				break;
			default:
				debug(D_BUG_RESOLVED, "trying next arg...\n");
				NEXT_ARG;
				IF_ARG_NOT_EXISTS break;
				sscanf(THIS_ARG, "%2s", s);
				switch (s[0]) {
					case 'u':
						opts.T *= 1e-6;
						break;
					case 'm':
						opts.T *= 1e-3;
						break;
					default: /* no unit */
						PREV_ARG;
						break;
				}
			}
		}

		else IF_ARG("f") goto freq;
		else IF_ARG("freq") goto freq;
		else IF_ARG("frequency") {
			freq:
			debug(D_INFO, "Parsing freq argument...");
			ARGV_COUNTER++;
			CHECK_ARGV;
			sscanf(argv[ARGV_COUNTER], "%lf%2s", &opts.T, s);
			debug(D_INFO, "Freq: got %lf (T=%lf)\n", opts.T,
					1.0/opts.T);
			opts.T = 1.0/opts.T;
			switch (s[0]) {
			case 'm':
				debug(D_INFO, "mHz\n");
				opts.T *= 1e3;
				break;
			case 'k':
				debug(D_INFO, "kHz\n");
				opts.T *= 1e-3;
				break;
			default:
				debug(D_INFO, "trying next arg...\n");
				NEXT_ARG;
				IF_ARG_NOT_EXISTS break;
				sscanf(THIS_ARG, "%2s", s);
				switch (s[0]) {
					case 'm':
						debug(D_INFO, "mHz\n");
						opts.T *= 1e3;
						break;
					case 'k':
						debug(D_INFO, "kHz\n");
						opts.T *= 1e-3;
						break;
					default: /* not here, rewind */
						PREV_ARG;
						break;
				}
			}
		}
		
		else IF_ARG("nper") goto buffer;
		else IF_ARG("nbuf") goto buffer;
		else IF_ARG("buf")  goto buffer;
		else IF_ARG("buffer") {
			buffer:
			NEXT_ARG_MUST_EXIST;
			if (!parse_long(THIS_ARG, &opts.dp_per_output))
				usage(argv[0], "couldn't parse long for nbuf");
		}
		
		else usage(argv[0], "unrecognized parameter on command line");
	}

	debug(D_INFO, "ENSURE_WF_EXISTS\n");
	for (int i = 0; i < N_DEV; i++) {
		ENSURE_WF_EXISTS(i);
		debug(D_INFO, "Set dev %d callback to <0x%llx>\n",
				i, (unsigned long long)opts.wf[i]);
	}

	debug(D_INFO, "Generating path names...\n");
	for (int i = 0; i < N_DEV; i++) {
		if (!opts.enabled[i]) continue;
		struct tm *tm = localtime(_local_time());
		tm->tm_year += 1900;
		tm->tm_mon++;
		sprintf(fnames[i], names[i], fmt_from_tm(tm));
		char *path = prepare_path(opts.dir_out, fnames[i]);
		debug(D_BUG_UNRESOLVED, "Have path at <0x%x>: %s\n", (unsigned long long) path, path);
		out[i] = fopen(path, "w");
		debug(D_INFO, "Have output file struct at <0x%x>\n", (unsigned long long) out[i]);
		fprintf(out[i], "%s\n", headers[i]);
		debug(D_INFO, "Wrote headers: %s\n", headers[i]);
		free(path);
	}

	debug(D_INFO, "Enabled devs: ");
	for (int i = 0; i < N_DEV; i++)
		if (opts.enabled[i])
			debug(D_INFO, "enabled dev: %d ", i);

	debug(D_INFO, "Starting to generate data...\n");

	char buf[64];
	memset(buf, 0, sizeof buf);
	for (int i = 0; i < N_DEV; i++)
		if (opts.enabled[i])
			strcat(buf, interfaces[i]), strcat(buf, " ");
	debug(D_NOTICE, TEXT_BOLD "Enabled interfaces: " COLOR_END "%s", buf);

	/* Loop forever (or if opts.n was set, until count > opts.n); *
	 * we expect to be killed by a signal otherwise.              */
	int count = 0;
	while (1) {

		if (opts.n && count >= opts.n)
			break;

		for (int i = 0; i < N_DEV; i++) {
			
			if (!opts.enabled[i])
				continue;

			debug(D_INFO, "Device %d is about to go live\n", i);
			
			/* Compute output and print */
			for (int k = 0; k < opts.dp_per_output; k++) {	

				timestamp(out[i]);

				for (int j = 0; j < num_dp[i]-1; j++) {

					debug(D_BUG_RESOLVED,
					      "Calling <0x%llx> (dev id=%d)\n",
					      (unsigned long long)opts.wf[i],
					      i);

					int _out = opts.wf[i](DEFAULT_AMPLITUDE,
							     opts.freq[i]);

					fprintf(out[i], "%d,", _out);
						//opts.wf[i](DEFAULT_AMPLITUDE,
					//		   opts.freq[i]));
				}

				fprintf(out[i], "%d\n",
					opts.wf[i](DEFAULT_AMPLITUDE,
						   opts.freq[i]));

				tick();
				count++;
			}

			/* if we don't call fflush(), client programs won't *
			 * see our updates, and our buffers will be dumped  *
			 * when we get killed                               */
			fflush(out[i]);
		}

		usleep((int)(opts.T * 1e6 * opts.dp_per_output));
	}
}

void _debug(int loglevel, char *file, const char *func,
	    char *clock, int line, char *msg, ...)
{
	/* check if verbose logging is enabled before *
	 * dumping everything into stdout 	      */
	if (loglevel == D_INFO         && !opts.verbose) return;
	if (loglevel == D_BUG_RESOLVED && !opts.verbose) return;

	/* naturally this is a variadic function */
	va_list args;
	char buffer[strlen(msg) + 1024];
	va_start(args, msg);
	vsnprintf(buffer, strlen(msg)+1024, msg, args);

	/* compute log tag length and prepare a buffer of *
	 * empty spaces to produce nice-looking logs      */
	size_t tag_len = strlen(log_tags[loglevel])
                       + strlen(file)
                       + strlen(func)
                       + ceil(log(line) / log(10.)) - 4;
	char *buf = malloc(tag_len + 1);
	memset(buf, ' ', tag_len);
	buf[tag_len] = 0;

	/* handle log tag */
	printf("%s %s:%d in %s() | ",
	       log_tags[loglevel], file, line, func);

	/* account for log tag on line breaks */
	char *to_print = strtok(buffer, "\n");
	printf("%s\n", to_print);

	while (to_print = strtok(NULL, "\n"))
		printf("%s| %s\n", buf, to_print);
}
