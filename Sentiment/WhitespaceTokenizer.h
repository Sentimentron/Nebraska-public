//
//  WhitespaceTokenizer.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__WhitespaceTokenizer__
#define __Sentiment__WhitespaceTokenizer__

#include <iostream>
#include <string>
#include <vector>

#include "ITokenizer.h"
#include "Sentence.h"

class WhitespaceTokenizer : public ITokenizer {
public:
    bool IsConsideredWhitespace(char c);
    WhitespaceTokenizer();
    ~WhitespaceTokenizer();
    virtual std::vector<IToken *> Tokenize(Sentence*);
};

#endif /* defined(__Sentiment__WhitespaceTokenizer__) */
