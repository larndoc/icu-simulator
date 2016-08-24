# GCC is horribly bugged and the build breaks if you put -lm
# anywhere else on the command line, so plz don't.
# as a side note since when are math libs not automatically linked?
all: fake-icu.c
	gcc -Wall fake-icu.c -o fake-icu -std=gnu11 -lm

.SILENT: clean
clean:
	rm -f /data/*.csv
	rm -f *.csv
	rm -f fake-icu
