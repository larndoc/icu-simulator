#ifndef _util_h
#define _util_h

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <tgmath.h>
#include <errno.h>
#include <limits.h>
#include "log.h"
#include "opts.h"

extern char *prepare_path(char *, char *);
extern void _usage(char *, int, const char *, const char *, const char *);
extern bool parse_long(char *, long *);
#define usage(name, reason) _usage(__FILE__, __LINE__, __func__, name, reason)

#endif
