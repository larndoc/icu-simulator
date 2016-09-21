#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdbool.h>
#include <tgmath.h>
#include <stdlib.h>
#include "log.h"

static const char *log_tags[]
			= { FG_BLUE   "[+] " COLOR_END,   /* INFO           */
			    FG_PURPLE "[-] " COLOR_END,   /* BUG RESOLVED   */
			    FG_YELLOW "[*] " COLOR_END,   /* NOTICE         */
		     TEXT_BOLD FG_RED "[!] " COLOR_END }; /* BUG UNRESOLVED */

void _debug(int loglevel, char *file, const char *func,
	    char *clock, int line, bool verbose, char *msg, ...)
{
	/* check if verbose logging is enabled before *
	 * dumping everything into stdout 	      */
	if (loglevel == D_INFO         && !verbose) return;
	if (loglevel == D_BUG_RESOLVED && !verbose) return;

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

	while ((to_print = strtok(NULL, "\n")) != NULL)
		printf("%s| %s\n", buf, to_print);
}
