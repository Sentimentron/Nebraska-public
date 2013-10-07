//
//  WordScorer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "SentiWordNetScorer.h"
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string.h>

//
// Constructors / destructors
//
SentiWordNetScorer::SentiWordNetScorer() {
    std::string default_path = std::string(S_DEFAULT_SENTIWORDNET_PATH);
    SentiWordNetReader swr(default_path);
    this->init(swr);
}

SentiWordNetScorer::SentiWordNetScorer(std::string path) {
    SentiWordNetReader swr;
    this->init(swr);
}

SentiWordNetScorer::~SentiWordNetScorer() {
    // Does nothing (yet)
}

//
// Misc functions
//
void SentiWordNetScorer::init(SentiWordNetReader &swr) {
    float       good, bad;
    std::string word, junk, line;
    std::ifstream input;
    std::map<std::string, std::vector<float>> intermediate_scores;
    
    auto contents = swr.GetContents();
    
    for (auto it = contents.begin(); it != contents.end(); it++) {
        std::string stp_word;
        std::vector<float> *map_entry;
        auto entry = *it;
        // Convert good and bad scores
        good = ::atof(entry[2].c_str());
        bad =  ::atof(entry[3].c_str());
        for (int i = 4; i < entry.size()-1; i++) {
            stp_word = entry[i].substr(0, entry[i].find("#"));
            map_entry = &(intermediate_scores[stp_word]);
            map_entry->push_back(good-bad);
        }
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
    }
}

void SentiWordNetScorer::enumerate(IStringEnumerator *e) {
    for(std::unordered_map<std::string, float>::const_iterator it = this->scores.begin();
        it != this->scores.end(); it++) {
        e->Enumerate(it->first);
    }
}

int SentiWordNetScorer::CreateScoringMap(IStringEnumerator *enumerator, size_t *smap_size, float **smap) {
    
    unsigned int required_size;
    
    // Make sure everything we have is in the enumerator
    this->enumerate(enumerator);
    required_size = enumerator->GetSize();
    
    // Check the scoring map is large enough
    if (*smap_size < required_size) {
        // If not, return the size and an error code
        *smap_size = required_size;
        return 1;
    }
    
    // Insert each score
    for(std::unordered_map<std::string, float>::const_iterator it = this->scores.begin();
        it != this->scores.end(); it++) {
        unsigned int id = enumerator->Enumerate(it->first);
        *(*smap + id) = it->second;
    }
    
    return 0;
}