#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <stdbool.h>

#define OVERFLOW(lim, var1, var2) if (var1 >= lim) {var1=0; var2++;}

char *get_date()
{
	static int year = 2016, month = 8, day = 1, hour = 12, minute = 1, second = 1, microsecond = 1;
	microsecond += 100;
	OVERFLOW(1000000, microsecond, second);
	OVERFLOW(60, second, minute);
	OVERFLOW(60, minute, hour);
	OVERFLOW(24, hour, day);
	OVERFLOW(30, day, month);
	OVERFLOW(12, month, year);
	char *ret = malloc(64);
	sprintf(ret, "%04d-%02d-%02dT%02d:%02d:%02d.%06d", year, month, day, hour, minute, second, microsecond);
	return ret;
}

int main()
{
	bool needs_header = false;
	srandom(time(NULL));
	
	if (access("fakedata.csv", F_OK) != 0) needs_header = true;

	FILE *f = fopen("fakedata.csv", "a");
	if (!f) {
		printf("ERR: no file");
		return 1;
	}

	if (needs_header) fprintf(f, "Time,x,y,z\n");
	
	while (1) {
		char *date = get_date();
		fprintf(f, "%s,%ld,%ld,%ld\n", date, random()%1024, random()%1024, random()%1024);
		fflush(f);
		free(date);
		usleep(100000);
	}
}
