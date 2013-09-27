//
//  SWTokenizer.h
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__SWTokenizer__
#define __Sentiment__SWTokenizer__

#include <set>
#include <iostream>
#include "WhitespaceTokenizer.h"

class SentiWordTokenizer : public WhitespaceTokenizer {
private:
    void init(std::string path);
    std::set<std::string> words;
    unsigned int largest_no_dashes = 0;
public:
    SentiWordTokenizer(std::string path) {
        this->init(path);
    }
    SentiWordTokenizer() {
        this->init("SentiWordNet_3.0.0_20120510.txt");
    }
    std::vector<IToken *> Tokenize(Sentence*);
};

#endif /* defined(__Sentiment__SWTokenizer__) */
