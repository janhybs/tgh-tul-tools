
RUN=./main

all:
	g++ -O3 -o $(RUN) main.cc

test: all
	@echo "RUNNING $(RUN): "
	@/usr/bin/time -f%e $(RUN) 2> duration
	@echo ""
	@echo "DURATION: "
	@cat duration
	