all: Twitter 

CFLAGS= -std=c++0x -I ../Nebraska -I ../randomc -c -g -O3
LDFLAGS= -L../Nebraska/Build -lNebraska -pthread

.PHONY: clean

clean:
	rm Twitter
	rm *.o

Twitter: Twitter.o
	$(CXX) $(LDFLAGS) -o Twitter Twitter.o

Twitter.o: Twitter.cpp
	$(CXX) $(CFLAGS) -o Twitter.o Twitter.cpp
