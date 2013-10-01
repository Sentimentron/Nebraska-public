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
#include "SentiWordTokenizer.h"

class TwitterTokenizer : public SentiWordTokenizer {
public:
    TwitterTokenizer(SentiwordNetReader &swr) : SentiWordTokenizer(swr) {}
    TwitterTokenizer(std::string path) : SentiWordTokenizer(path) {}
    TwitterTokenizer() : SentiWordTokenizer() {}
    std::vector<IToken *>Tokenize(Sentence *);
};

#endif /* defined(__Sentiment__TwitterTokenizer__) */
