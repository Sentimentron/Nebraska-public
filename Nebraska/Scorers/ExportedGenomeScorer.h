//
//  ExportedGenomeScorer.h
//  Sentiment
//
//  Created by Richard Townsend on 30/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__ExportedGenomeScorer__
#define __Sentiment__ExportedGenomeScorer__

#include "Interfaces/IScorer.h"
#include "Interfaces/IStringEnumerator.h"
#include <iostream>
#include <unordered_map>

class ExportedGenomeScorer : public IScorer {
private:
    void init(std::string path);
    void enumerate(IStringEnumerator *);
    std::unordered_map<std::string, float> scores;
public:
    ExportedGenomeScorer(std::string);
    // Version which takes a path to a SentiwordNetFile
    int CreateScoringMap(IStringEnumerator *, size_t *, float **);
};

#endif /* defined(__Sentiment__ExportedGenomeScorer__) */
