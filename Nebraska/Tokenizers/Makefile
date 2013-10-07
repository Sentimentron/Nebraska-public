OBJS = SentiWordTokenizer.o TwitterTokenizer.o WhitespaceTokenizer.o

all: $(OBJS)

%.o: %.cpp
	$(CXX) $(CFLAGS) $< -o $(PRODUCTS_DIR)/$@
