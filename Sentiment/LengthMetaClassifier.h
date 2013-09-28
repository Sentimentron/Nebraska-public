//
//  LengthMetaClassifier.h
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_LengthMetaClassifier_h
#define Sentiment_LengthMetaClassifier_h

#include "IMetaClassifier.h"
#include "EnumeratedSentence.h"

template <class T, unsigned int D>
class LengthMetaClassifier : public IMetaClassifier<T> {
private:
    unsigned int ComputeClassifierId(const EnumeratedSentence *s, float *score_map) {
        unsigned int sen_length = (unsigned int)s->GetEnumeratedVector().size();
        return sen_length / D;
    }
public:
};

#endif
