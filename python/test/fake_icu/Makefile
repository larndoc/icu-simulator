all: fake-icu.c
	gcc -Wall fake-icu.c -o fake-icu -lm

.SILENT: clean
clean:
	rm -f /data/*.csv
	rm -f *.csv
	rm -f fake-icu
