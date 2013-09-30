//
//  ExportedGenomeScorer.cpp
//  Sentiment
//
//  Created by Richard Townsend on 30/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "ExportedGenomeScorer.h"
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string.h>
#include <string>

//
// Constructors / destructors
//
ExportedGenomeScorer::ExportedGenomeScorer(std::string path) {
    this->init(path);
}


//
// Misc functions
//
void ExportedGenomeScorer::init(std::string path) {
    
    // Stream representing the exported genome on disk
    std::ifstream input;
    input.open(path);
    
    std::string word;
    float score;
    int junk;
    
    while (input >> word >> junk >> score) {
        this->scores[word] = score; 
    }
    
    input.close();
}

void ExportedGenomeScorer::enumerate(IStringEnumerator *e) {
    for(std::unordered_map<std::string, float>::const_iterator it = this->scores.begin();
        it != this->scores.end(); it++) {
        e->Enumerate(it->first);
    }
}

int ExportedGenomeScorer::CreateScoringMap(IStringEnumerator *enumerator, size_t *smap_size, float **smap) {
    
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