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
#include "SentiWordNetReader.h"
#include "WhitespaceTokenizer.h"

class SentiWordTokenizer : public WhitespaceTokenizer {
private:
    void init(SentiwordNetReader &);
    std::set<std::string> words;
    unsigned int largest_no_dashes = 0;
protected:
    std::vector<std::string> SplitWhitespace(Sentence *);
    std::vector<std::string> ResolveTokensInDictionary(std::vector<std::string>);
public:
    SentiWordTokenizer(SentiwordNetReader &swr) {
        this->init(swr);
    }
    SentiWordTokenizer(std::string path) {
        SentiwordNetReader swr(path);
        this->init(swr);
    }
    SentiWordTokenizer() {
        SentiwordNetReader swr;
        this->init(swr);
    }
    std::vector<IToken *> Tokenize(Sentence*);
};

#endif /* defined(__Sentiment__SWTokenizer__) */
