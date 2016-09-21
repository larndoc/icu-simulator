# GCC is horribly bugged and the build breaks if you put -lm
# anywhere else on the command line, so plz don't.
# as a side note since when are math libs not automatically linked?

SRCS = fake-icu.c ae.c lmathx.c log.c
TRGT = fake-icu
INCL = /usr/include/lua5.3
LIBS = /usr/lib/x86_64-linux-gnu/

all: fake-icu.c
	gcc -Wall $(SRCS) -I$(INCL) -L$(LIBS) -o $(TRGT) -std=gnu11 -lm -llua5.3

.SILENT: clean
clean:
	rm -f /data/*.csv
	rm -f fake-icu
