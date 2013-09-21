//
//  WordScorer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "SentiWordScorer.h"
#include <fstream>
#include <sstream>
#include <string.h>

const char * const S_DEFAULT_SENTIWORDNET_PATH = "SentiWordNet_3.0.0_20120510.txt";

//
// Constructors / destructors
//
SentiWordScorer::SentiWordScorer() {
    std::string default_path = std::string(S_DEFAULT_SENTIWORDNET_PATH);
    this->init(default_path);
}

SentiWordScorer::SentiWordScorer(std::string path) {
    this->init(path);
}

SentiWordScorer::~SentiWordScorer() {
    // Does nothing (yet)
}

//
// Misc functions
//
void SentiWordScorer::init(std::string path) {
    float       good, bad;
    std::string word, junk, line;
    std::ifstream input;
    // Open the input file
    input.open(path);
    while (getline(input, line)) {
        std::stringstream s;
        if(line[0] == '#') continue;
        s << line;
        // Extract the relevant parts
        s >> junk >> junk >> good >> bad >> word;
        if (fabs(good) < 0.005 && fabs(bad) < 0.005) {
            continue; 
        }
        std::cout << word << "\t" << good << "\t" << bad << "\n";
    }
}

int SentiWordScorer::CreateScoringMap(IStringEnumerator *e, size_t *s, float **f) {
    return -1;
}