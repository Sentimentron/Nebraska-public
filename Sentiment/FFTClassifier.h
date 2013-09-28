//
//  Classifier.h
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__Classifier__
#define __Sentiment__Classifier__

#include <tuple>
#include <iostream>
#include "EnumeratedSentence.h"
#include "FloatingFloatBuffer.h"
#include "IClassifier.h"


class FFTClassifier : public IClassifier {
private:
    bool negative_seen = false;
    bool positive_seen = false;
    std::vector<std::tuple<const EnumeratedSentence*, FloatingFloatBuffer *>>training;
    FloatingFloatBuffer *CreateSignal(const EnumeratedSentence *, float *);
public:
    FFTClassifier ();
    ~FFTClassifier();
    ClassificationLabel Classify(const EnumeratedSentence *, float *score_map);
    void Train(const EnumeratedSentence *, float *);
    void Detrain();
};

#endif /* defined(__Sentiment__Classifier__) */
