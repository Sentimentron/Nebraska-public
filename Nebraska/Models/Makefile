OBJS = EnumeratedSentence.o FloatingFloatBuffer.o Sentence.o TokenizedSentence.o WordToken.o

all: $(OBJS)

%.o: %.cpp
	$(CXX) $(CFLAGS) $< -o $(PRODUCTS_DIR)/$@
