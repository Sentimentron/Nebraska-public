//
//  WhitespaceTokenizer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include <string>
#include <vector>

#include "Sentence.h"
#include "WhitespaceTokenizer.h"
#include "WordToken.h"

//
// Constructors and destructors 
//

WhitespaceTokenizer::WhitespaceTokenizer() {
    // No initialization necessary
}

WhitespaceTokenizer::~WhitespaceTokenizer() {
    // No cleanup necessary (ain't that grand?)
}

//
// Other stuff
//

bool is_considered_whitespace(char c) {
    // Helper function, takes a character and determines whether
    // it's whitespace or not. When something is whitespace, that's
    // used to split the input Sentence
    switch (c) {
    case ' ':
        return true;
    case '\t':
        return true;
    case '.':
        return true;
    default:
        return false;
    }
}

std::vector<IToken *> WhitespaceTokenizer::Tokenize(Sentence *s) {
    std::vector<IToken *> ret;
    std::string buf; 
    std::string text = s->GetText();
    for (int i = 0; i < text.length(); i++) {
        bool is_space = is_considered_whitespace(text[i]);
        if (is_space) {
            if(!buf.length()) continue;
            WordToken *w = new WordToken(buf);
            ret.push_back(w);
            buf = "";
            continue;
        }
        buf += text[i];
    }
    if(buf.length()) {
        WordToken *w = new WordToken(buf);
        ret.push_back(w);
    }
    return ret;
}