//
//  WordToken.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "WordToken.h"
#include <string>

//
// Constructors and destructors
//
WordToken::WordToken(std::string word) {
    this->word = word;
}

WordToken::~WordToken() {
    // Does nothing (memory should be free'd by WordTokenizer)
}

//
// Other stuff
//
std::string WordToken::GetKey() {
    // GetKey provides a feature used for scoring
    return this->word; 
}