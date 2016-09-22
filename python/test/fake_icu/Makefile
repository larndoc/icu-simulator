# GCC is horribly bugged and the build breaks if you put -lm
# anywhere else on the command line, so plz don't.
# as a side note since when are math libs not automatically linked?

SRCS = $(wildcard *.c)
OBJS = $(SRCS:.c=.o)
INCL = /usr/include/lua5.3
LIBS = /usr/lib/x86_64-linux-gnu/
TRGT = fake-icu
CC = gcc
CFLAGS = -Wall -Werror -I$(INCL) -std=gnu11
LDFLAGS = -L$(LIBS) -lm -llua5.3

all: $(TRGT)

$(TRGT): $(OBJS)
	gcc $(OBJS) $(LDFLAGS) -o $(TRGT) 

%.o: %.c %.h
	$(CC) $(CFLAGS) -c $<

%.o: %.c
	$(CC) $(CFLAGS) -c $<

.SILENT: cleanall
cleanall:
	rm -f /data/*.csv
	rm -f $(TRGT)
	rm -f $(OBJS)
.SILENT: clean
clean:
	rm -f $(TRGT)
	rm -f $(OBJS)
.SILENT: cleanobjs
cleanobjs:
	rm -f $(OBJS)
