//
//  SignMetaClassifier.h
//  Sentiment
//
//  Created by Richard Townsend on 25/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__SignMetaClassifier__
#define __Sentiment__SignMetaClassifier__

#include <iostream>
#include "IMetaClassifier.h"
#include <map>

int sign_count(EnumeratedSentence *s, float *smap);

template <class T>
class SignMetaClassifier : public IMetaClassifier<T> {
private:
    unsigned int ComputeClassifierId(EnumeratedSentence *s, float *score_map) {
        return sign_count(s, score_map);
    }
public:
};

#endif /* defined(__Sentiment__SignMetaClassifier__) */
