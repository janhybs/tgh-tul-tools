
RUN=./main

all:
	gcc -O3 -o $(RUN) main.c

test: all
	@echo "RUNNING $(RUN): "
	@/usr/bin/time -f%e $(RUN) 2> duration
	@echo ""
	@echo "DURATION: "
	@cat duration
	