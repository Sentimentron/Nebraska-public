//
//  Sentence.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "Sentence.h"

//
// Sentence constructors
//
Sentence::Sentence(ClassificationLabel label, char *text) {
    this->text  = text;
    this->label = label;
}

Sentence::Sentence(int label, char *text) {
    ClassificationLabel l;
    if (label == 1) {
        l = PositiveSentenceLabel;
    }
    else if (label == -1) {
        l = NegativeSentenceLabel;
    }
    else {
        l = UndefinedSentenceLabel;
    }
    this->text = text;
    this->label = l;
}

Sentence::~Sentence() {
    free(this->text);
}

ClassificationLabel Sentence::GetClassification() {
    return this->label;
}

const char *Sentence::GetClassificationStr() {
    switch (this->GetClassification()) {
        case NegativeSentenceLabel:
            return "Negative";
        case PositiveSentenceLabel:
            return "Positive";
        default:
            return "Unknown";
    }
}

std::string Sentence::GetText() {
    return std::string(this->text);
}