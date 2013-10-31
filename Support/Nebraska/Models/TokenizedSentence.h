//
//  TokenizedSentence.h
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__TokenizedSentence__
#define __Sentiment__TokenizedSentence__

#include <iostream>
#include "Models/Sentence.h"
#include "Interfaces/IToken.h"
#include "Interfaces/ITokenizer.h"

class TokenizedSentence : public Sentence {
private:
    std::vector<IToken *> tokens;
    Sentence *parent;
public:
    TokenizedSentence (Sentence *, ITokenizer *);
    ~TokenizedSentence();
    std::vector<IToken *> GetTokens();
};

#endif /* defined(__Sentiment__TokenizedSentence__) */
