//
//  EnumeratedSentence.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "EnumeratedSentence.h"

//
// Constructors
//

EnumeratedSentence::~EnumeratedSentence() {
    delete this->parent;
}

EnumeratedSentence::EnumeratedSentence(TokenizedSentence *s, IStringEnumerator *e) : Sentence(s) {
    std::vector<IToken *> tokens = s->GetTokens();
    for (std::vector<IToken *>::const_iterator it = tokens.begin();
         it != tokens.end(); it++) {
        unsigned int id = e->Enumerate((*it)->GetKey());
        this->mapping.push_back(id);
    }
    this->parent = s;
}