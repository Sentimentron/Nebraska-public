CXX=g++
CXXFLAGS=-g -std=c++11 -O3 -ffast-math 
LDFLAGS=-lsqlite3

Cluster: main.o
	$(CXX) $(LDFLAGS) -o Cluster *.o

.PHONY deploy: Cluster
	mv -v Cluster ../../Build
