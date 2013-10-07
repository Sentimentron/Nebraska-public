//
//  SWTokenizer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "Models/WordToken.h"
#include "SentiWordTokenizer.h"
#include "Input/SentiWordNetReader.h"
#include <fstream>
#include <sstream>
#include <stack>

// copied from http://rosettacode.org/wiki/Count_occurrences_of_a_substring#C.2B.2B
// returns count of non-overlapping occurrences of 'sub' in 'str'
int countSubstring(const std::string& str, const std::string& sub)
{
    if (sub.length() == 0) return 0;
    int count = 0;
    for (size_t offset = str.find(sub); offset != std::string::npos;
         offset = str.find(sub, offset + sub.length()))
    {
        ++count;
    }
    return count;
}

int setContainsString (const std::string& member, const std::set<std::string> &in) {
    auto it = in.find(member);
    if (it == in.end()) return 0;
    return 1;
}

void SentiWordTokenizer::init(SentiWordNetReader &swr) {
    this->largest_no_dashes = 0;
    
    auto contents = swr.GetContents();
    
    for (auto it = contents.begin(); it != contents.end(); it++) {
        std::string stp_word;
        auto entry = *it;
        // Convert good and bad scores
        for (int i = 4; i < entry.size()-1; i++) {
            stp_word = entry[i].substr(0, entry[i].find("#"));
            int dash_count = countSubstring(stp_word, "_");
            if (!dash_count) continue;
            this->words.insert(stp_word);
            if (dash_count > this->largest_no_dashes) {
                this->largest_no_dashes = dash_count;
            }
        }
    }
}

std::vector<std::string> SentiWordTokenizer::SplitWhitespace(Sentence *s) {
    std::string text = s->GetText();
    std::string buf;
    std::vector<std::string> split_wbuf;

    for (int i = 0; i < text.length(); i++) {
        bool is_space = this->IsConsideredWhitespace(text[i]);
        if (is_space) {
            if(!buf.length()) continue;
            split_wbuf.push_back(buf);
            buf = "";
            continue;
        }
        buf += text[i];
    }
    
    if(buf.length()) {
        split_wbuf.push_back(buf);
    }
    
    return split_wbuf;
}

std::vector<std::string> SentiWordTokenizer::ResolveTokensInDictionary(std::vector<std::string> split_wbuf) {
    std::string buf = "";
    std::vector<std::string> ret;
    for (int i = 0; i < split_wbuf.size(); i++) {
        if(!split_wbuf[i].length()) continue;
        buf = "" + split_wbuf[i];
        std::stack<std::string> candidates;
        candidates.push(split_wbuf[i]);
        for (int j = 1; j < this->largest_no_dashes; j++) {
            if (i + j >= split_wbuf.size()) break;
            buf += "_" + split_wbuf[i+j];
            if (setContainsString(buf, this->words)) {
                candidates.push(buf);
            }
        }
        std::string word = candidates.top();
        unsigned int no_dashes = countSubstring(word, "_");
        i += no_dashes;
        ret.push_back(word);
    }
    return ret;
}

std::vector<IToken *> SentiWordTokenizer::Tokenize(Sentence *s) {
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
        ret.push_back(new WordToken(*it));
    }
    
    return ret;
}