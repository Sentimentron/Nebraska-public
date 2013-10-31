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
#include "Input/SentiWordNetReader.h"
#include "WhitespaceTokenizer.h"

class SentiWordNetTokenizer : public WhitespaceTokenizer {
private:
    void init(SentiWordNetReader &);
    std::set<std::string> words;
    unsigned int largest_no_dashes;
protected:
    std::vector<std::string> SplitWhitespace(Sentence *);
    std::vector<std::string> ResolveTokensInDictionary(std::vector<std::string>);
public:
    SentiWordNetTokenizer(SentiWordNetReader &swr) {
        this->init(swr);
    }
    SentiWordNetTokenizer(std::string path) {
        SentiWordNetReader swr(path);
        this->init(swr);
    }
    SentiWordNetTokenizer() {
        SentiWordNetReader swr;
        this->init(swr);
    }
    std::vector<IToken *> Tokenize(Sentence*);
};

#endif /* defined(__Sentiment__SWTokenizer__) */
