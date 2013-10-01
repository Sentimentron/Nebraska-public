//
//  EnumeratedSentence.h
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__EnumeratedSentence__
#define __Sentiment__EnumeratedSentence__

#include <vector>
#include <iostream>
#include "IStringEnumerator.h"
#include "Sentence.h"
#include "TokenizedSentence.h"

class EnumeratedSentence : public Sentence {
private:
    std::vector<unsigned int> mapping;
    TokenizedSentence *parent;
public:
    const std::vector<unsigned int> GetEnumeratedVector() const {
        return this->mapping;
    };
    TokenizedSentence *GetParent() {
        return this->parent;
    };
    EnumeratedSentence(TokenizedSentence *, IStringEnumerator *);
    ~EnumeratedSentence();
};

#endif /* defined(__Sentiment__EnumeratedSentence__) */
