//
//  HMStringEnumerator.cpp
//  Sentiment
//
//  Created by Richard Townsend on 18/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include <string>
#include "HMStringEnumerator.h"

HMStringEnumerator::HMStringEnumerator() {
    // Initializes current identifier
    this->identifier = 0;
}

HMStringEnumerator::~HMStringEnumerator() {
    // Currently doesn't do anything
}

unsigned int HMStringEnumerator::Enumerate(std::string s) {
    // Enumerate assigns s a number, which makes lookups
    // (i.e. accessing a score) faster later
    std::unordered_map<std::string, unsigned int>::const_iterator forward_it;
    
    // First of all, check if it's already been enumerated
    forward_it = this->forward_map.find(s);
    if (forward_it != this->forward_map.end()) {
        // Great! Found it.
        return this->forward_map[forward_it->first];
    }
    
    // If it hasn't, insert it into the forward map
    this->forward_map[s] = this->identifier;
    
    // Push it into the reverse_map vector, where it should
    // be stored at the same offset
    this->reverse_map.push_back(s);
    
    // Increment and return the identifier
    return this->identifier++;
}