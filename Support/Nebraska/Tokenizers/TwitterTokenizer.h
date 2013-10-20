//
//  TwitterTokenizer.h
//  Sentiment
//
//  Created by Richard Townsend on 01/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__TwitterTokenizer__
#define __Sentiment__TwitterTokenizer__

#include <iostream>
#include "SentiWordNetTokenizer.h"

class TwitterTokenizer : public SentiWordNetTokenizer {
public:
    TwitterTokenizer(SentiWordNetReader &swr) : SentiWordNetTokenizer(swr) {}
    TwitterTokenizer(std::string path) : SentiWordNetTokenizer(path) {}
    TwitterTokenizer() : SentiWordNetTokenizer() {}
    std::vector<IToken *>Tokenize(Sentence *);
};

#endif /* defined(__Sentiment__TwitterTokenizer__) */
