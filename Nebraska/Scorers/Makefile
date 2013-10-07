OBJS = ExportedGenomeScorer.o SentiWordNetScorer.o

all: $(OBJS)

%.o: %.cpp
	$(CXX) $(CFLAGS) $< -o $(PRODUCTS_DIR)/$@
