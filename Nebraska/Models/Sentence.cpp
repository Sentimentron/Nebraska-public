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

Sentence::Sentence(Sentence *s) {
    this->text = s->text;
    this->label = s->label;
    this->free_text = false;
}

void Sentence::CopyStringToInternal(const char *text) {
    size_t length = strlen(text);
    this->text = (char *)calloc(length + 1, 1);
    memcpy(this->text, text, length);
}

Sentence::Sentence(ClassificationLabel label, const char *text) {
    this->CopyStringToInternal(text);
    this->label = label;
    this->free_text = true;
}

Sentence::Sentence(int label, const char *text) {
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
    this->CopyStringToInternal(text);
    this->label = l;
    this->free_text = true;
}

Sentence::~Sentence() {
    if(this->free_text) {
        free(this->text);
    }
}


//
// Sentence methods
//
const ClassificationLabel Sentence::GetClassification() const {
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