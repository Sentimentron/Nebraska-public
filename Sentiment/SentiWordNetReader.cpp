//
//  SentiWordNetReader.cpp
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "SentiWordNetReader.h"
#include <fstream>
#include <sstream>

void SentiwordNetReader::init() {
    std::ifstream input;
    std::string buf, line;
    std::vector<std::string> vbuf;
    std::vector<std::string> pbuf;
    input.open(this->path);
    while (getline(input, line)) {
        std::string stp_word;
        if(line[0] == '#') continue;
        for (int i = 0; i < line.size(); i++) {
            if (line[i] == '\t' || line[i] == '\n') {
                vbuf.push_back(buf);
                buf = "";
                continue;
            }
            buf += line[i];
        }
        if (buf.length()) {
            vbuf.push_back(buf);
            buf = "";
        }
        
        bool word_encountered = false;
        for (auto it = vbuf.begin(); it != vbuf.end(); it++) {
            bool is_word = false;
            std::string entry = *it;
            for (int i = 0; i < it->size(); i++) {
                if(entry[i] == '#') {
                    is_word = true;
                    break;
                }
            }
            if (!is_word || word_encountered) {
                pbuf.push_back(entry);
                continue;
            }
            
            if (word_encountered) break;
            
            buf = "";
            for (int i = 0; i < it->size(); i++) {
                std::string entry = *it;
                if(entry[i] == ' ') {
                    pbuf.push_back(buf);
                    buf = "";
                    continue;
                }
                buf += entry[i];
            }
            if (buf.length()) {
                pbuf.push_back(buf);
                buf = "";
            }
            word_encountered = true;
        }
        
        
        this->contents.push_back(pbuf);
        vbuf.clear(); pbuf.clear();
    }
}

