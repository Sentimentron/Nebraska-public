//
//  Classifier.h
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__Classifier__
#define __Sentiment__Classifier__

#include <iostream>
#include "TokenizedSentence.h"

class Classifier {
private:
    std::vector<TokenizedSentence *>training;
public:
    Classifier (std::vector<TokenizedSentence *>training);
    ClassificationLabel Classify(TokenizedSentence *, float *score_map);
    //float SelfAssess();
};

#endif /* defined(__Sentiment__Classifier__) */
