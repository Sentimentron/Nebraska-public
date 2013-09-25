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


class Classifier : public IClassifier {
private:
    std::vector<std::tuple<EnumeratedSentence*, FloatingFloatBuffer *>>training;
    FloatingFloatBuffer *CreateSignal(EnumeratedSentence *, float *);
public:
    Classifier ();
    ClassificationLabel Classify(EnumeratedSentence *, float *score_map);
    void Train(EnumeratedSentence *, float *);
};

#endif /* defined(__Sentiment__Classifier__) */
