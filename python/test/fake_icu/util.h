#ifndef _util_h
#define _util_h

static inline char *prepare_path(char *path, char *fname)
{
	size_t to_alloc = strlen(path) + strlen(fname) + 2;
	char *ret = malloc(to_alloc);
	for (int i = 0; i < to_alloc; i++)
		ret[i] = 0;
	strcat(ret, path);
	if (path[strlen(path)-1] != '/')
		strcat(ret, "/");
	strcat(ret, fname);
	debug(D_BUG_RESOLVED, "Prepared path: %s\nat <0x%x>", ret, (unsigned long long) ret);
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
		"\taw           \n"
		"\tarbwf        \n"
		"\tawf          Produce an arbitrary waveform\n"
		"\t             Usage: awf [expr]"
		"\t             Where [expr] is some function of t in Lua\n"
		"\t             e.g. sin(4*t)+cos(3*t)-t*t\n"
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
		"\t%s fib fob pcu w fib \"sin(t)\" t 250ms\n"
		"\t%s fib_hk fsc_sci wave fib_hk random\n"
		"\t%s fob_hk freq 128 Hz wf fob_hk sine 0.5 noise\n"
		"--------------------------------------------------------\n"
		"If you're seeing this, something probably went wrong.\n"
		"If so, the error was here: %s:%d, in a call to %s().\n"
		"Here's the reason we were called: %s\n",
		name, name, name, name, file, line, func, reason);
	exit(1);
}

static inline bool parse_long(char *str, long *ret)
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

#endif
