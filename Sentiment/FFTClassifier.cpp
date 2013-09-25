//
//  Classifier.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "math.h"
#include "FFTClassifier.h"
#include "EnumeratedSentence.h"

//
// Classifier constructors
//

Classifier::Classifier() {

}

//
// Classifier misc methods
//

float correlation(FloatingFloatBuffer &x, FloatingFloatBuffer &y, unsigned int length) {
    // Use pearson's correlation c.f.
    float mean_x, mean_y;
    float var_x, var_y;
    float ret = 0.0f;
    float var_div_x = 0.0f, var_div_y = 0.0f;
    
    mean_x = x.ComputeMean();
    mean_y = y.ComputeMean();
    
    var_x = x.ComputeVariance();
    var_y = y.ComputeVariance();
    
    for(int i = 0; i < length; i++) {
        ret += (x[i] - mean_x) * (y[i] - mean_y);
        var_div_x += (x[i] - var_x) * (x[i] - var_x);
        var_div_y += (y[i] - var_y) * (y[i] - var_y);
    }
    
    return ret / (sqrtf(var_div_x) * sqrtf(var_div_y));
}

float autocorrelation(FloatingFloatBuffer &x, FloatingFloatBuffer &y, int *offset) {
    float max_correlation = 0.0f;
    int max_offset = 0;
    int max_length = x.GetLength();
    FloatingFloatBuffer *shortest = &y;
    if (y.GetLength() > max_length) {
        max_length = y.GetLength();
        shortest = &x;
    }
    for (int i = 0; i < max_length >> 2; i++) {
        float c;
        shortest->SetStartOffset(i);
        c = correlation(x, y, max_length);
        if (c > max_correlation) {
            max_correlation = c;
            max_offset = i;
        }
    }
    if (offset != NULL) {
        *offset = max_offset;
    }
    return max_correlation;
}

FloatingFloatBuffer *Classifier::CreateSignal(EnumeratedSentence *s, float *score_map) {
    auto sentence_items = s->GetEnumeratedVector();
    FloatingFloatBuffer *bf = new FloatingFloatBuffer();
    for (auto it = sentence_items.begin();
         it != sentence_items.end(); it++) {
        bf->Append(*(score_map + *it));
    }
    return bf;
}

void Classifier::Train(EnumeratedSentence *s, float *score_map) {
    
    ClassificationLabel r = this->Classify(s, score_map);
    if (r == s->GetClassification()) {
        return; // No need to train!
    }
    
    FloatingFloatBuffer *bf = this->CreateSignal(s, score_map);
    this->training.push_back(std::make_tuple(s, bf));
}

ClassificationLabel Classifier::Classify (EnumeratedSentence *s, float *score_map) {
    ClassificationLabel ret;
    
    float best_corr = 0.0f;
    
    auto training_pairs = this->training;
    auto classify_signal = this->CreateSignal(s, score_map);
    
    if(!this->training.size()) {
        return UndefinedSentenceLabel;
    }
    
    if (s->GetClassification() == NegativeSentenceLabel) {
        std::cout << "Classifying something negative!\n";
    }
    
    for (auto it = training_pairs.begin(); it != training_pairs.end(); it++) {
        auto t = *it;
        auto signal = std::get<1>(t);
        auto corr = autocorrelation(*classify_signal, *signal, NULL);
        if (corr > best_corr) {
            best_corr = corr;
            ret = std::get<0>(t)->GetClassification();
        }
    }
    
    return ret;
}