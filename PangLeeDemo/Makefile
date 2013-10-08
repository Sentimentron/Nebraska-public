all: PangLee 

CFLAGS= -std=c++0x -o PangLee -I ../Nebraska -I ../randomc -c -g -O3
LDFLAGS= -L../Nebraska/Build -lNebraska -pthread

.PHONY: clean

clean:
	rm PangLee
	rm *.o

PangLee: PangLee.o
	$(CXX) $(LDFLAGS) -o PangLee PangLee.o

PangLee.o: PangLee.cpp
	$(CXX) $(CFLAGS) -o PangLee.o PangLee.cpp
