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

int _debug(int loglevel, char *file, const char *func,
	    char *clock, int line, bool verbose, char *msg, ...)
{
	if ((loglevel == D_INFO || loglevel == D_BUG_RESOLVED)
	    && !verbose) return 1;
	
	char tag[128];
	sprintf(tag, "%s %s:%d in %s()", log_tags[loglevel], file, line, func);
	printf("%s", tag);
	int len = strlen(tag);
	memset(tag, 0, 128);
	memset(tag, ' ', len > 50 ? len : 50);
	/* check if verbose logging is enabled before *
	 * dumping everything into stdout 	      */

	va_list args;
	char buffer[strlen(msg) + 1024];
	va_start(args, msg);
	vsnprintf(buffer, strlen(msg)+1024, msg, args);

	char *to_print = strtok(buffer, "\n");
	printf(" | %s\n", to_print);

	while ((to_print = strtok(NULL, "\n")) != NULL)
		printf("%s | %s\n", tag, to_print);

	return 0;
}
