//
//  IClassifier.h
//  Sentiment
//
//  Created by Richard Townsend on 25/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_IClassifier_h
#define Sentiment_IClassifier_h

#include "EnumeratedSentence.h"

class IClassifier {
public:
    virtual ~IClassifier() {}
    virtual ClassificationLabel Classify(EnumeratedSentence *, float *) = 0;
    virtual void Train(EnumeratedSentence *, float *) = 0;
    virtual void Detrain() = 0;
};

#endif
