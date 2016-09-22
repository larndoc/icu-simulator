#ifndef _log_h
#define _log_h

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
int _debug(int, char *, const char *, char *, int, bool, char *,...);
#define debug(level, ...) _debug(level, __FILE__, __func__, NULL, __LINE__, opts.verbose, \
				 __VA_ARGS__);


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

#endif /* !defined _log_h */
