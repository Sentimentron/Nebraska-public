//
//  sentence_loader.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__sentence_loader__
#define __Sentiment__sentence_loader__

#include <iostream>
#include <vector>
#include <string>
#include "sentence.h"

typedef enum {
    SentenceReadFileError,
    SentenceReadFormatError,
    SentenceReadAllocationError,
    SentenceReadOk
} SentenceReadStatus;

class ISentenceSource {
public:
    virtual ~ISentenceSource() {}
    virtual std::vector<Sentence *> GetSentences() = 0;
};

class PLSentenceSource : public ISentenceSource {
    /* Pang-Lee sentence source */
private:
    // Private initialization functions etc...
    SentenceReadStatus  init(char *path);
    std::vector<Sentence *> sentences;
public:
    PLSentenceSource(char *path);
    PLSentenceSource();
    ~PLSentenceSource();
    std::vector<Sentence *> GetSentences();
};


#endif /* defined(__Sentiment__sentence_loader__) */
