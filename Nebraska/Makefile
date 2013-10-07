#
# Nebraska, non-XCode MakeFile

include Makefile.in

all: Nebraska

OBJS=Products Classifiers Enumerators Evaluators Input Models Models Scorers Tokenizers Evolver RandomC
.PHONY: $(OBJS) clean

Nebraska: $(OBJS)
	$(CXX) -shared -o $(PRODUCTS_DIR)/libNebraska $(PRODUCTS_DIR)/*.o

Products:
	mkdir -p $(PRODUCTS_DIR)

clean: 
	rm -R $(PRODUCTS_DIR)

Classifiers:
	$(MAKE) -C Classifiers

Enumerators:
	$(MAKE) -C Enumerators

Evaluators:
	$(MAKE) -C Evaluators

Input:
	$(MAKE) -C Input

Models:
	$(MAKE) -C Models

Scorers:
	$(MAKE) -C Scorers

Tokenizers:
	$(MAKE) -C Tokenizers

Evolver:
	$(CXX) $(CFLAGS) -o $(PRODUCTS_DIR)/Evolver.o Evolver.cpp

RandomC:
	$(CXX) $(CFLAGS) -o $(PRODUCTS_DIR)/sfmt.o ../randomc/sfmt.cpp