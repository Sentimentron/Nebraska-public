//
//  ITokenizer.h
//  Sentiment
//
//  Created by Richard Townsend on 08/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_IScorer_h
#define Sentiment_IScorer_h

#include "Interfaces/IStringEnumerator.h"

class IScorer {
public:
    virtual ~IScorer() {}
    virtual int CreateScoringMap(IStringEnumerator *, size_t *, float **) = 0;
}; 

#endif
