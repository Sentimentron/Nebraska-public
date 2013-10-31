OBJS = PLSentenceSource.o SentiWordNetReader.o SSentenceSource.o

all: $(OBJS)

%.o: %.cpp
	$(CXX) $(CFLAGS) $< -o $(PRODUCTS_DIR)/$@
