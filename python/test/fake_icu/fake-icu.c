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
#include "ae.h"
#include "log.h"
#include "opts.h"
#include "util.h"
#include "tm.h"
#include "wf.h"

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
#define ENSURE_WF_EXISTS(d) if(!(opts.enabled[d]&&!opts.wf[d])); else opts.wf[d]="sin(t)"
#define PARSE_WAVE do { NEXT_ARG_MUST_EXIST; opts.waveforms[opts.num_wf++].name = THIS_ARG; NEXT_ARG_MUST_EXIST; opts.waveforms[opts.num_wf].expr = THIS_ARG;} while (0) 

struct _opts opts;
struct timestamp tzero, now;

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

	debug(D_INFO, "This is\ntesting the\nlogging facility.");

	debug(D_INFO, "Setting default opts...\n");
	opts.T = 0.1f;
	opts.dir_out = "/data/";
	opts.n = 0;
	opts.dp_per_output = 1;
	opts.noise_ampl = 0;
	opts.num_wf = 0;
	for (int j = 0; j < N_DEV; j++) {
		opts.enabled[j] = false;
		opts.wf[j] 	= NULL;
		opts.freq[j]    = 0.0f;
	}

	for (int k = 0; k < N_DEV*32; k++)
		opts.waveforms[k] = (struct _wf) {NULL, NULL};

	/* start the lua interpreter */
	ae_open();

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
			NEXT_ARG_MUST_EXIST;
			char *dev = strtok(THIS_ARG, ":");
			char *name = strtok(NULL, ":");
			debug(D_BUG_UNRESOLVED, "wf: parsed %s:%s\n", dev, name);
			NEXT_ARG_MUST_EXIST;
			opts.waveforms[opts.num_wf].dev = dev;
			opts.waveforms[opts.num_wf].name = name;
			opts.waveforms[opts.num_wf].expr = THIS_ARG;
			opts.num_wf++;
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
	for (int i = 0; i < N_DEV; i++)
		ENSURE_WF_EXISTS(i);

	debug(D_INFO, "Generating path names...\n");
	for (int i = 0; i < N_DEV; i++) {
		if (!opts.enabled[i]) continue;
		struct tm *tm = localtime(_local_time());
		tm->tm_year += 1900;
		tm->tm_mon++;
		sprintf(fnames[i], names[i], fmt_from_tm(tm));
		char *path = prepare_path(opts.dir_out, fnames[i]);
		debug(D_BUG_RESOLVED, "Have path at <0x%x>: %s\n", (unsigned long long) path, path);
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

			debug(D_INFO, "Device %d (%s) is about to go live\n",
			      i, interfaces[i]);
			
			/* Compute output and print */
			for (int k = 0; k < opts.dp_per_output; k++) {	

				timestamp(out[i]);

				for (int j = 0; j < num_dp[i]-1; j++) {
					debug(D_BUG_RESOLVED, "eval maj/min %d,%d", i, j);
					double _out = eval_by_major_minor(i, j);
					debug(D_BUG_RESOLVED, "Have result %lf\n", _out);
					fprintf(out[i], "%lf,", _out);
						//opts.wf[i](DEFAULT_AMPLITUDE,
					//		   opts.freq[i]));
				}

				fprintf(out[i], "%lf\n", eval_by_major_minor(i,
									     num_dp[i]-1));
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
	ae_close();
	return 0;
}

