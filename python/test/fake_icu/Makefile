all: fake-icu.c
	gcc -Wall fake-icu.c -o fake-icu -std=gnu11 -lm

.SILENT: clean
clean:
	rm -f /data/*.csv
	rm -f *.csv
	rm -f fake-icu
