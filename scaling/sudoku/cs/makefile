
RUN=mono ./main.exe

all:
	gmcs main.cs

test: all
	@echo "RUNNING $(RUN): "
	@/usr/bin/time -f%e $(RUN) 2> duration
	@echo ""
	@echo "DURATION: "
	@cat duration
	