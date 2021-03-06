//
//  Classifier.cpp
//  Sentiment
//
//  Created by Richard Townsend on 21/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "math.h"
#include "Classifiers/FFTClassifier.h"
#include "Models/EnumeratedSentence.h"

//
// Classifier constructors
//

FFTClassifier::FFTClassifier() {
    this->positive_seen = false;
    this->negative_seen = false;
}

FFTClassifier::~FFTClassifier() {
    this->Detrain();
}

//
// Classifier misc methods
//

float correlation(FloatingFloatBuffer &x, FloatingFloatBuffer &y, unsigned int length, unsigned short offset,
                  float mean_x, float mean_y, float var_x, float var_y) {
    // Use pearson's correlation c.f.
    float ret = 0.0f;
    float var_div_x = 0.0f, var_div_y = 0.0f;
    
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
    if (y.GetLength() > max_length) {
        max_length = y.GetLength();
    }
    float mean_x = x.ComputeMean();
    float mean_y = y.ComputeMean();
    float var_x = x.ComputeVariance();
    float var_y = y.ComputeVariance();
    
    for (int i = 0; i < max_length >> 2; i++) {
        float c;
        c = correlation(x, y, max_length, i, mean_x, mean_y, var_x, var_y);
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

FloatingFloatBuffer *FFTClassifier::CreateSignal(const EnumeratedSentence *s, float *score_map) {
    auto sentence_items = s->GetEnumeratedVector();
    float *ret = (float *)malloc(sentence_items.size() * sizeof(float));
    int c = 0;
    for (auto it = sentence_items.begin();
         it != sentence_items.end(); it++) {
        *(ret + c++) = *(score_map + *it);
    }
    return new FloatingFloatBuffer(ret, (unsigned int)sentence_items.size());
}

void FFTClassifier::Train(const EnumeratedSentence *s, float *score_map) {
    FloatingFloatBuffer *bf = this->CreateSignal(s, score_map);
    this->negative_seen |= s->GetClassification() == NegativeSentenceLabel;
    this->positive_seen |= s->GetClassification() == PositiveSentenceLabel;
    this->training.push_back(std::make_tuple(s, bf));
}

void FFTClassifier::Detrain() {
    for (auto it = this->training.begin(); it != this->training.end(); it++) {
        auto sig = std::get<1>(*it);
        delete sig;
    }
    this->training.clear();
}

ClassificationLabel FFTClassifier::Classify (const EnumeratedSentence *s, float *score_map) {
    ClassificationLabel ret = UndefinedSentenceLabel;
    const EnumeratedSentence *best_match;
    
    float best_corr = 0.0f;
    if (!this->negative_seen || !this->positive_seen) {
        return UndefinedSentenceLabel;
    }
    auto training_pairs = this->training;
    auto classify_signal = this->CreateSignal(s, score_map);
    
    if(!this->training.size()) {
        delete classify_signal;
        return UndefinedSentenceLabel;
    }
    
    for (auto it = training_pairs.begin(); it != training_pairs.end(); it++) {
        auto t = *it;
        auto signal = std::get<1>(t);
        auto corr = autocorrelation(*classify_signal, *signal, NULL);
        if (corr > best_corr) {
            best_corr = corr;
            ret = std::get<0>(t)->GetClassification();
            best_match = std::get<0>(t);
        }
    }
    
    delete classify_signal;
    
    //if (fabs(best_corr) < 0.20) return UndefinedSentenceLabel;
    
    return ret;
}
