//
//  TokenizedSentence.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "TokenizedSentence.h"

//
// TokenizedSentence constructors
//

TokenizedSentence::TokenizedSentence(Sentence *parent, ITokenizer *tok) : Sentence(parent) {
    this->tokens = tok->Tokenize(parent);
}

TokenizedSentence::~TokenizedSentence() {
}

//
// TokenizedSentence misc functions
//

std::vector<IToken *>TokenizedSentence::GetTokens() {
    return this->tokens;
}