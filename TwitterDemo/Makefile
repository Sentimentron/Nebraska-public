all: Twitter TwitterCrossEvolve

CFLAGS= -std=c++0x -I ../Nebraska -I ../randomc -c -g -O3
LDFLAGS= -L../Nebraska/Build -lNebraska -pthread

.PHONY: clean

clean:
	rm Twitter
	rm TwitterCrossEvolve
	rm *.o

Twitter: Twitter.o
	$(CXX) $(LDFLAGS) -o Twitter Twitter.o
	
TwitterCrossEvolve: TwitterCrossEvolve.o
	$(CXX) $(LDFLAGS) -o TwitterCrossEvolve TwitterCrossEvolve.o

Twitter.o: Twitter.cpp
	$(CXX) $(CFLAGS) -o Twitter.o Twitter.cpp

TwitterCrossEvolve.o:
	$(CXX) $(CFLAGS) -o TwitterCrossEvolve.o TwitterCrossEvolve.cpp
