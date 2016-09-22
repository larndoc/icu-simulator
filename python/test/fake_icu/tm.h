#ifndef _tm_h
#define _tm_h

struct timestamp {
	long y,  /* year        */
	     mo, /* month       */
	     d,  /* day         */
	     h,  /* hour        */
	     mi, /* minute      */
	     s,  /* second      */
	     us; /* microsecond */
};

extern struct timestamp tzero, now;

#define is_leap_year(x) ((x%400) || (!(x%4) && (x%100)))
#define wrap(var, lim, of) if (var < lim); else { var = fmod(var, lim); of++; }
static inline void tick()
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

static inline void timestamp(FILE *f)
{
	fprintf(f, "%04ld-%02ld-%02ldT%02ld:%02ld:%02ld.%06ld,",
		now.y, now.mo, now.d, now.h, now.mi,
		now.s, now.us + random() % US_JITTER);
}

#define clk() _ts_to_s(now)
static inline double _ts_to_s(struct timestamp ts)
{
	return ts.h * 3600.0
	     + ts.mi *  60.0
	     + (double) ts.s
	     + ts.us / 1e6;
}

#endif /* !defined _tm_h */
