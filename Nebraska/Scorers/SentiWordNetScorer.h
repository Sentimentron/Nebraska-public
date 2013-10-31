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
#include "Interfaces/IScorer.h"
#include "Interfaces/IStringEnumerator.h"
#include "Input/SentiWordNetReader.h"

class SentiWordNetScorer : public IScorer {
private:
    void init(SentiWordNetReader &swr);
    void enumerate(IStringEnumerator *);
    std::unordered_map<std::string, float> scores;
public:
    SentiWordNetScorer();
    ~SentiWordNetScorer();
    SentiWordNetScorer(SentiWordNetReader &swr) {
        this->init(swr);
    }
    // Version which takes a path to a SentiwordNetFile
    SentiWordNetScorer(std::string);
    int CreateScoringMap(IStringEnumerator *, size_t *, float **);
};

#endif /* defined(__Sentiment__WordScorer__) */
