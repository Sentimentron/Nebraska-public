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
#include <vector>
#include <map>
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
    std::map<std::string, std::vector<float>> intermediate_scores;
    // Open the input file
    input.open(path);
    while (getline(input, line)) {
        std::stringstream s;
        std::string stp_word;
        std::vector<float> *map_entry;
        if(line[0] == '#') continue;
        s << line;
        // Extract the relevant parts
        s >> junk >> junk >> good >> bad >> word;
        if (fabs(good) < 0.005 && fabs(bad) < 0.005) {
            // There's no point in wasting space if there's no score
            continue; 
        }
        // Now need to remove the sense tag
        stp_word = word.substr(0, word.find("#"));
        // Insert score into intermediate map
        map_entry = &(intermediate_scores[stp_word]);
        map_entry->push_back(good - bad);
    }
    // Go through each intermediate score and average it
    for(std::map<std::string, std::vector<float>>::const_iterator it = intermediate_scores.begin();
        it != intermediate_scores.end(); it++) {
        unsigned long length;
        float average = 0.0f;
        length = it->second.size();
        for(std::vector<float>::const_iterator s = it->second.begin();
            s != it->second.end(); s++) {
            average += *s;
        }
        average /= length;
        this->scores[it->first] = average;
        std::cout << it->first << "\t" << average << "\n";
    }
}

int SentiWordScorer::CreateScoringMap(IStringEnumerator *e, size_t *s, float **f) {
    return -1;
}