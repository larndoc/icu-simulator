#ifndef _wf_h
#define _wf_h
#include "log.h"
extern double eval(char *);
extern char * wf_get_expr(const char *, const char *);
static inline double eval_by_major_minor(int major, int minor)
{
	debug(D_BUG_RESOLVED, "major %d, minor %d\n", major, minor);
	return eval(wf_get_expr(interfaces[major], header_strs[major][minor]));
}
#endif /* !defined _wf_h */
