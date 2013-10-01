//
//  ISentenceSource.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_ISentenceSource_h
#define Sentiment_ISentenceSource_h
#include "Sentence.h"
class ISentenceSource {
public:
    virtual ~ISentenceSource() {}
    virtual std::vector<Sentence *> GetSentences() = 0;
};
#endif
