#include <stdbool.h>
#include <stdlib.h>
#include <tgmath.h>
#include <string.h>
#include "opts.h"
#include "wf.h"
#include "ae.h"
#include "tm.h"
#include "log.h"

double eval(char *expr)
{
	if (!expr) return sin(clk());
	ae_set("t", clk());
	return ae_eval(expr);
}

char *wf_get_expr(const char *dev, const char *name)
{
	for (int i = 0; i < opts.num_wf; i++) {
		/* per-data col exprs */
		if (!strcasecmp(opts.waveforms[i].name, name)
		    && !strcasecmp(opts.waveforms[i].dev, dev))
		    	return opts.waveforms[i].expr;
		/* whole-device exprs */
		if (opts.waveforms[i].name == NULL
		    && !strcasecmp(opts.waveforms[i].dev, dev))
		    	return opts.waveforms[i].expr;
	}

	return NULL;
}
