//
//  ITokenizer.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_ITokenizer_h
#define Sentiment_ITokenizer_h

#include <vector>
#include "IToken.h" 
#include "Sentence.h"

class ITokenizer {
public:
    virtual ~ITokenizer() {}
    virtual std::vector<IToken *> Tokenize(Sentence*) = 0;
};

#endif
