#
# Nebraska, non-XCode MakeFile

include Makefile.in

all: Nebraska

OBJS=Products Classifiers Enumerators Evaluators Input Models Interfaces Models Scorers Tokenizers Evolver
.PHONY: $(OBJS) clean

Nebraska: $(OBJS)

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

Interfaces:
	$(MAKE) -C Interfaces

Models:
	$(MAKE) -C Models

Scorers:
	$(MAKE) -C Scorers

Tokenizers:
	$(MAKE) -C Tokenizers

Evolver:
	$(CPP) $(CFLAGS) -o $(PRODUCTS_DIR)/Evolver.o Evolver.cpp
