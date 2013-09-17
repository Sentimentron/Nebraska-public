//
//  Sentence.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__Sentence__
#define __Sentiment__Sentence__

#include <iostream>

typedef enum {
    PositiveSentenceLabel,
    NegativeSentenceLabel,
    UndefinedSentenceLabel
} ClassificationLabel;

class Sentence {
private:
    char                *text;
    ClassificationLabel label;
public:
    Sentence (ClassificationLabel, char *);
    Sentence (int, char *);
    ~Sentence();
    ClassificationLabel GetClassification();
    const char* GetClassificationStr();
    std::string GetText();
};

#endif /* defined(__Sentiment__Sentence__) */
