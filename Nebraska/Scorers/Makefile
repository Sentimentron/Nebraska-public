OBJS = ExportedGenomeScorer.o SentiWordScorer.o

all: $(OBJS)

%.o: %.cpp
	$(CXX) $(CFLAGS) $< -o $(PRODUCTS_DIR)/$@
