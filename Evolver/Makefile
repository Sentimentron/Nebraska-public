all: Evolver 

CFLAGS= -std=c++0x -o Evolver -I ../Nebraska -I ../randomc -c -g 
LDFLAGS= -L../Nebraska/Build -lNebraska -pthread

.PHONY: clean

clean:
	rm Evolver
	rm *.o

Evolver: Evolver.o
	$(CXX) $(LDFLAGS) -o Evolver Evolver.o

Evolver.o: Evolver.cpp
	$(CXX) $(CFLAGS) -o Evolver.o Evolver.cpp
