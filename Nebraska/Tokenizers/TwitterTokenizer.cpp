//
//  TwitterTokenizer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 01/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "TwitterTokenizer.h"
#include "WordToken.h"

std::vector<IToken *> TwitterTokenizer::Tokenize(Sentence *s) {
    std::vector<std::string> split_wbuf, tokens;
    std::string buf;
    std::string text = s->GetText();
    std::vector<IToken *> ret;
    
    // Phase 1: split text based on whitespace
    split_wbuf = this->SplitWhitespace(s);
    
    // Phase 2: peek ahead largest_no_dashes for each token
    // and see if a more complex SentiWordNet token can be created
    tokens = this->ResolveTokensInDictionary(split_wbuf);
    
    // Phase 3: convert to ITokens
    for (auto it = tokens.begin(); it != tokens.end(); it++) {
        auto str = *it;
        if (str[0] == '#' || str[0] == '@') {
            ret.push_back(new WordToken(""));
            continue;
        };
        ret.push_back(new WordToken(str));
    }
    
    return ret;
}