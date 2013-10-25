CXX=clang++
CXXFLAGS=-g -std=c++0x -stdlib=libc++ -O3 -ffast-math 
LDFLAGS=-lsqlite3 -stdlib=libc++ 

Cluster: main.o
	$(CXX) $(LDFLAGS) -o Cluster *.o

deploy: Cluster
	mv -v Cluster ../../Build

.PHONY clean:
	rm -f *.o
	rm -f Cluster