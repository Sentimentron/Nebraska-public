//
//  WordScorer.h
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__WordScorer__
#define __Sentiment__WordScorer__

#include <unordered_map>
#include <string>
#include <iostream>
#include "IStringEnumerator.h"
#include "SentiWordNetReader.h"

class SentiWordScorer {
private:
    void init(SentiwordNetReader &swr);
    void enumerate(IStringEnumerator *);
    std::unordered_map<std::string, float> scores;
public:
    SentiWordScorer();
    ~SentiWordScorer();
    SentiWordScorer(SentiwordNetReader &swr) {
        this->init(swr);
    }
    // Version which takes a path to a SentiwordNetFile
    SentiWordScorer(std::string);
    int CreateScoringMap(IStringEnumerator *, size_t *, float **);
};

#endif /* defined(__Sentiment__WordScorer__) */
