//
//  Classifier.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "Classifier.h"

//
// Classifier constructors
//

Classifier::Classifier(std::vector<TokenizedSentence *>t) {
    this->training = t;
}

//
// Classifier misc methods
//

ClassificationLabel Classifier::Classify (TokenizedSentence *s, float *score_map) {
    return UndefinedSentenceLabel;
}