#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <tgmath.h>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdarg.h>

/* FIXME: square wave generator is broken;
 * returns 1024 for 10 or so points, then
 * 0 for only two (duty cycle > 50%).
 */

/* FIXME: find a GENSYM macro that works */
#define ARGV_COUNTER _argv_counter 
#define LOOP_ARGV for (int ARGV_COUNTER = 1; ARGV_COUNTER < argc; ARGV_COUNTER++)
#define IF_ARG(x) if (!strcasecmp(argv[ARGV_COUNTER], x))
#define IF_NOT_ARG(x) if (strcasecmp(argv[ARGV_COUNTER], x))
#define CHECK_ARGV if (ARGV_COUNTER >= argc) usage(argv[0])
#define PARSE_WAVE(wf,f) do{debug(D_INFO, "Incrementing argument counter...\n"); ARGV_COUNTER++; CHECK_ARGV;    	\
			IF_ARG("sine") { debug(D_BUG_RESOLVED, "Got sine\n");  wf = sine;     }		\
			else IF_ARG("square") { debug(D_BUG_RESOLVED, "Got square\n"); wf = square;	}	\
			else IF_ARG("sawtooth") { debug(D_BUG_UNRESOLVED, "Got sawtooth\n"); wf = sawtooth;}	\
			else IF_ARG("random") { debug(D_INFO, "Got random\n");wf = _random;}		\
			else usage(argv[0]);			\
			IF_NOT_ARG("random") {			\
			ARGV_COUNTER++; CHECK_ARGV;		\
			f=atof(argv[ARGV_COUNTER]);		\
			debug(D_INFO, "parsed freq %f\n", f);}} while (0)
#define ENSURE_WF_EXISTS(id) if (opts.enabled[id] && !opts.wf[id]) opts.wf[id] = _random

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


#define fmt_from_tm(tm) tm->tm_year, tm->tm_mon, tm->tm_mday, tm->tm_hour, tm->tm_min, tm->tm_sec

/* pretty-printing debugging stuff */
void _debug(int, char *, const char *, char *, int, char *, ...);
#define debug(level, ...) _debug(level, __FILE__, __func__, NULL, __LINE__, __VA_ARGS__);
const char *log_tags[ ] = {	"[+] ",	"[-] ",  "[*] ",  "[!] "};
			/*	 INFO	RESOLVED  NOTICE  UNRESOLVED */

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

struct timeval _tv, _tv_orig;
#define init_clk() (gettimeofday(&_tv_orig, NULL))
#define clk() (gettimeofday(&_tv, NULL), (double)(_tv.tv_sec - _tv_orig.tv_sec) + 1e-6*(_tv.tv_usec - _tv_orig.tv_usec))

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
		"Time,Sensor_Laser,Laser_Micro,Zeeman,Sci_Data_ID,Sci_Data,Timestamp",
		/* FIB HK */
		"Time,Status_HB,Status_LB,LUP_cnt,P1V5,P3V3,P5V,N5V,P8V,P12V,P1I5,P3I3,P5I,"
		"N5I,P8I,P12I,TE,TS1,TS2,Checksum,CMD_exec_cnt,ICU_err_cnt,Last_cmd,Last_err,HK_req_cnt,sync_count",
		/* FOB HK */
		"Time,FOB",
		/* FSC HK */
		"Time,Peregrine_Lock,Sensor_Temp_A,Sensor_Temp_B,Sensor_Temp_Duty_Cycle,Laser_Temp_A,Laser_Temp_B,"
		"Laser_Temp_Duty_Cycle,"
		"Laser_Current,Laser_Current_Zero_Cross,Microwave_Ref,Microwave_Ref_Zero_Cross,Zeeman_Freq_Zero_Cross,"
		"PCB_Temp_A,PCB_Temp_B,Laser_Diode_Voltage,Diode_Optical_Power,P2V4,P3V3,P8V,N8V,P12V,PCB_Temp_C,"
		"PCB_Temp_D,PCB_Temp_E,ICU_Checksum,ICU_Command_Count,ICU_Sync_Count",
		/* PCU HK */
		"Time,I_FIB,I_FOB,I_FSC,I_P3V3,I_FIBH,I_FOBH,I_FSCH,I_P1V8,Temp,V_P2V4,V_P3V3,V_P12V,V_P8V,V_N8V,V_P5V,V_N5V"
};

/* number of data points to generate by device */
const int num_dp[N_DEV] = {4, 4, 6, 25, 1, 27, 16};

/* data generator function prototype */
typedef int (*data_generator_func_t)(int, double);

/* global options structure */
struct {
	bool enabled[N_DEV]; 
	data_generator_func_t wf[N_DEV];
	double freq[N_DEV];
	double time_between_samples;
	char *dir_out;
	bool verbose;
	char min_priority;
	unsigned int n;
} opts;

int sine(int A, double f)
{
	double t = clk();
	debug(D_BUG_UNRESOLVED, "clk(): t=%lf\n", t);
	int ret = A * sin(2*M_PI*f*t);
	return ret;
}

int square(int A, double f)
{
	// I ASSURE YOU THIS SOMETIMES WORKS
	double y = sine(1, f);
	return y > 0 ? A
		: (fabs(y) < 1.0f ? A/2 : 0);
}

int sawtooth(int A, double f)
{
	// THIS? ALMOST NEVER
	double t = clk();
	double T = 1/f;
	t  = fmodf(t, T);
	return A * ((f*t) - floor(f*t));
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
	debug(D_BUG_RESOLVED, "Prepared path: %s\n", ret);
	return ret;
}

void usage(char *name)
{
	fprintf(stderr,
			"%s: fake data streams for all your testing needs.\n"
			"Problems? Contact me: <he915@ic.ac.uk>.\n"
			"All parts can be referenced as {part}{_hk,_sci,}"
			"Options:\n"
			"\tfib		Produce fake FIB data\n"
			"\tfob		Produce fake FOB data\n"
			"\tfsc		Produce fake FSC data\n"
			"\tpcu		Produce fake PCU data\n"
			"\tw		Specify waveform to produce for target device\n"
			"\twaveform	\"\n"
			"\t             Usage: wave [part] [wave_type] [freq]\n"
			"\t             Where [part] in {fib, fob, fsc, pcu},\n"
			"\t                   [wave_type] in {square, sine, sawtooth, random}\n"
			"\t                   [freq] is a double; don't supply to random waveforms\n"
			"\tf		\n"
			"\tfile         Specify file output path\n"
			"\t             Usage: file [path]\n"
			"\t             Where [path] is a path to desired output folder\n"
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
			"\t             Note that time and freq options supercede each other;\n"
			"\t                 this program will only use the value calculated\n"
			"\t                 from the last option specified on the command line"
			"\tn\n"
			"\tnumber       Number of data points to print.\n"
			"\t             Usage: number [nr]\n"
			"\t             Where [nr] is an integer\n"
			"Example usage:\n"
			"\t%s fib fob pcu wave fib square 10 wave fob sine 25 f /data/ t 250ms\n"
			"\t%s fib_hk fsc_sci wave fib_hk random",
			name, name, name
	);
	exit(1); 
}

int main(int argc, char *argv[])
{
	char s[2];
	FILE *out[N_DEV];
	char fnames[N_DEV][64];

	srandom(time(NULL));
	
	init_clk();
	
	debug(D_INFO, "This is\ntesting the\nlogging facility.");
	
	debug(D_INFO, "Setting default opts...\n");
	opts.time_between_samples = 0.1f;
	opts.dir_out = "/data/";
	opts.n = 0; // no limit
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
		debug(D_INFO, "Parsing args with ARGV_COUNTER=%d\n", ARGV_COUNTER);
		// these opts enable entire interfaces
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

		// these handle specific modules
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
			ARGV_COUNTER++;
			CHECK_ARGV;
			opts.n = atoi(argv[ARGV_COUNTER]);
		}

		// waveform generator specifying
		else IF_ARG("w")    goto waveform;
		else IF_ARG("wave") goto waveform;
		else IF_ARG("waveform") {
			waveform:
			debug(D_INFO, "Got waveform; parsing...\n");
			ARGV_COUNTER++;
			CHECK_ARGV;
			IF_ARG("fib")
				PARSE_WAVE(opts.wf[FIB_SCI] = opts.wf[FIB_HK], opts.freq[FIB_SCI] = opts.freq[FIB_HK]);
			else IF_ARG("fob")
				PARSE_WAVE(opts.wf[FOB_SCI] = opts.wf[FOB_HK], opts.freq[FOB_SCI] = opts.freq[FOB_HK]);
			else IF_ARG("fsc")
				PARSE_WAVE(opts.wf[FSC_SCI] = opts.wf[FSC_HK], opts.freq[FSC_SCI] = opts.freq[FSC_HK]);
			else IF_ARG("fib_sci") PARSE_WAVE(opts.wf[FIB_SCI], opts.freq[FIB_SCI]);
			else IF_ARG("fob_sci") PARSE_WAVE(opts.wf[FOB_SCI], opts.freq[FOB_SCI]);
			else IF_ARG("fsc_sci") PARSE_WAVE(opts.wf[FSC_SCI], opts.freq[FSC_SCI]);
			else IF_ARG("fib_hk")  PARSE_WAVE(opts.wf[FIB_HK],  opts.freq[FIB_HK]);
			else IF_ARG("fob_hk")  PARSE_WAVE(opts.wf[FOB_HK],  opts.freq[FOB_HK]);
			else IF_ARG("fsc_hk")  PARSE_WAVE(opts.wf[FSC_HK],  opts.freq[FSC_HK]);
			else IF_ARG("pcu")     PARSE_WAVE(opts.wf[PCU_HK],  opts.freq[PCU_HK]);
			else usage(argv[0]);   /* error */
		}

		// specify file output path (default: ./)
		else IF_ARG("f") goto file;
		else IF_ARG("file") {
			file:
			ARGV_COUNTER++;
			CHECK_ARGV;
			opts.dir_out = argv[ARGV_COUNTER];
			debug(D_INFO, "filepath: got %s\n", opts.dir_out);
		}

		// TODO: specify frequency at which to supply new data
		// this is gonna be a pain and a half
		//
		// specify time to wait between new data points (default: 100ms)
		else IF_ARG("t") goto time;
		else IF_ARG("time") {
			time:
			debug(D_BUG_RESOLVED, "Parsing time argument...");
			ARGV_COUNTER++;
			CHECK_ARGV;
			sscanf(argv[ARGV_COUNTER], "%lf%2s", &opts.time_between_samples, s);
			debug(D_INFO, "Time: got %lf ", opts.time_between_samples);
			switch (s[0]) {
				case 'u':
					debug(D_BUG_RESOLVED, "us\n");
					opts.time_between_samples *= 1e-6;
					break;
				case 'm':
					debug(D_BUG_RESOLVED, "ms\n");
					opts.time_between_samples *= 1e-3;
					break;
				default:
					debug(D_BUG_UNRESOLVED, "NO UNIT: attempting to parse the next argument... ");
					if (ARGV_COUNTER == argc-1) break; // we got seconds
					ARGV_COUNTER++;
					sscanf(argv[ARGV_COUNTER], "%2s", s);
					switch (s[0]) {
						case 'u':
							debug(D_BUG_RESOLVED, "us\n");
							opts.time_between_samples *= 1e-6;
							break;
						case 'm':
							debug(D_BUG_RESOLVED, "ms\n");
							opts.time_between_samples *= 1e-3;
							break;
						default: // no unit -> next on the cmd line is something else
							debug(D_BUG_RESOLVED, "no unit; decrementing argument counter...\n");
							ARGV_COUNTER--;
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
			sscanf(argv[ARGV_COUNTER], "%lf%2s", &opts.time_between_samples, s);
			debug(D_INFO, "Freq: got %lf (T=%lf)\n", opts.time_between_samples,
					1.0/opts.time_between_samples);
			opts.time_between_samples = 1.0/opts.time_between_samples;
			switch (s[0]) {
				case 'm':
					debug(D_INFO, "mHz\n");
					opts.time_between_samples *= 1e3;
					break;
				case 'k':
					debug(D_INFO, "kHz\n");
					opts.time_between_samples *= 1e-3;
					break;
				default:
					debug(D_INFO, "NO UNIT: attempting to parse the next argument... ");
					if (ARGV_COUNTER == argc-1) break; // we got seconds
					ARGV_COUNTER++;
					sscanf(argv[ARGV_COUNTER], "%2s", s);
					switch (s[0]) {
						case 'm':
							debug(D_INFO, "mHz\n");
							opts.time_between_samples *= 1e3;
							break;
						case 'k':
							debug(D_INFO, "kHz\n");
							opts.time_between_samples *= 1e-3;
							break;
						default:
							debug(D_INFO, "no unit; decrementing argument counter...\n");
							ARGV_COUNTER--;
							break;
					}
			}
			
		} else usage(argv[0]);
	}

	debug(D_INFO, "ENSURE_WF_EXISTS\n");
	for (int i = 0; i < N_DEV; i++) {
		ENSURE_WF_EXISTS(i);
		debug(D_INFO, "Set dev %d callback to <0x%llx>\n", i, (unsigned long long)opts.wf[i]);
	}

	debug(D_INFO, "Generating path names...\n");
	for (int i = 0; i < N_DEV; i++) {
		if (!opts.enabled[i]) continue;
		struct tm *tm = localtime(_local_time());
		tm->tm_year += 1900;
		tm->tm_mon++;
		sprintf(fnames[i], names[i], fmt_from_tm(tm));
		char *path = prepare_path(opts.dir_out, fnames[i]);
		out[i] = fopen(path, "w");
		fprintf(out[i], "%s\n", headers[i]);
		debug(D_INFO, "Wrote headers: %s\n", headers[i]);
		free(path);
	}

	debug(D_INFO, "Enabled devs: ");
	for (int i = 0; i < N_DEV; i++)
		if (opts.enabled[i])
			debug(D_INFO, "enabled dev: %d ", i);

	debug(D_INFO, "Starting to generate data...\n");
	
	/* Loop forever (or if opts.n was set, until count > opts.n); *
	 * we expect to be killed by a signal otherwise.              */	
	int count = 0;
	while (1) {
		if (opts.n && count >= opts.n) break;
		for (int i = 0; i < N_DEV; i++) {
			if (!opts.enabled[i]) continue;
			debug(D_INFO, "Device %d is about to generate output\n", i);
			
			/* Get local data */
			struct timeval tv;
			gettimeofday(&tv, NULL);
			struct tm tm = *localtime(_local_time());
			
			/* fix dates -> counts from epoch in 1900 */
			tm.tm_year += 1900;
			tm.tm_mon++;
			
			debug(D_BUG_RESOLVED, "Have timestamp %04d-%02d-%02dT%02d:%02d:%02d.%06ld",
					tm.tm_year, tm.tm_mon, tm.tm_mday,
					tm.tm_hour, tm.tm_min, tm.tm_sec,
					tv.tv_usec);
			
			fprintf(out[i], "%04d-%02d-%02dT%02d:%02d:%02d.%06ld,",
					tm.tm_year, tm.tm_mon, tm.tm_mday,
					tm.tm_hour, tm.tm_min, tm.tm_sec,
					tv.tv_usec);
		
			/* Compute output and print */
			for (int j = 0; j < num_dp[i]-1; j++) {
				debug(D_INFO, "Calling <0x%llx> (dev id=%d)\n",
						(unsigned long long)opts.wf[i], i);
				fprintf(out[i], "%d,", opts.wf[i](DEFAULT_AMPLITUDE, opts.freq[i]));
			}
			
			fprintf(out[i], "%d\n", opts.wf[i](DEFAULT_AMPLITUDE, opts.freq[i]));
			
			/* if we don't call fflush(), client programs won't *
			 * see our updates, and our buffers will be dumped  *
			 * when we get killed                               */
			fflush(out[i]);
		}
		count++;
		usleep((int)(opts.time_between_samples * 1e6));
	}
}

void _debug(int loglevel, char *file, const char *func, char *clock, int line, char *msg, ...)
{
	/* check if verbose logging is enabled before *
	 * dumping everything into stdout 	      */
	if (loglevel == D_INFO && !opts.verbose) return;
	if (loglevel == D_BUG_RESOLVED && !opts.verbose) return;

	va_list args;
	va_start(args, msg);
	
	char buffer[strlen(msg) + 1024];
	vsnprintf(buffer, strlen(msg)+1024, msg, args);	

	switch (loglevel) {
		case D_BUG_UNRESOLVED:
			printf(TEXT_BOLD FG_RED);
			break;
		case D_NOTICE:
			printf(FG_RED);
			break;
		case D_BUG_RESOLVED:
			printf(FG_YELLOW);
			break;
		case D_INFO:
			printf(FG_BLUE);
			break;
	}
	printf("%s ", log_tags[loglevel]);
	printf(COLOR_END);	
	printf("%16s() < -%12s:%3d|\t", func, file, line);
	char *to_print = strtok(buffer, "\n");
	printf("%s\n", to_print);
	// strtok() will return NULL after
	// the string is entirely tokenized
	while ((to_print = strtok(NULL, "\n"))) {
		for (int i = 0; i < 43; i++) printf(" ");
		printf("|\t%s", to_print);
	}
}
