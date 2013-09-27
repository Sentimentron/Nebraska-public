//
//  IEvaluationFramework.h
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_IEvaluationFramework_h
#define Sentiment_IEvaluationFramework_h

#include <map>
#include <vector>
#include <string>
#include "IClassifier.h"
#include "EnumeratedSentence.h"
#include <exception>
#include <iostream>

class EvaluationResult {
private:
    std::map<EnumeratedSentence *, ClassificationLabel> results;
    float Percent(unsigned int num, unsigned int div) {
        if (!div) {div = 1; num = 0;}
        return 100.0f * num / div;
    }
public:
    void PushResult(EnumeratedSentence *s, ClassificationLabel l) {
        this->results[s] = l;
    }
    unsigned int TotalSentencesTrained;
    unsigned int TotalSentencesTested() {
        return (unsigned int)results.size();
    }
    float ComputeFitness() {
        return this->TotalCorrectByLabel(PositiveSentenceLabel) + this->TotalCorrectByLabel(NegativeSentenceLabel);
    }
    unsigned int TotalSentencesCorrect() {
        unsigned int ret = 0;
        for(auto it = this->results.begin(); it != this->results.end(); it++) {
            auto sentence = it->first;
            auto label = it->second;
            if (label == UndefinedSentenceLabel) continue;
            if (sentence->GetClassification() == label) ret++;
        }
        return ret;
    }
    unsigned int TotalCorrectByLabel(ClassificationLabel l) {
        unsigned int ret = 0;
        for (auto it = this->results.begin(); it != this->results.end(); it++) {
            auto sentence = it->first;
            auto label = it->second;
            if (sentence->GetClassification() != l) continue;
            if (l == label) ret++;
        }
        return ret;
    }
    unsigned int TotalByLabel(ClassificationLabel l) {
        unsigned int ret = 0;
        for (auto it = this->results.begin(); it != this->results.end(); it++) {
            auto label = it->second;
            if (label == l) ret++;
        }
        return ret;
    }
    unsigned int TotalDefined() {
        unsigned int ret = 0;
        for (auto it = this->results.begin(); it != this->results.end(); it++) {
            auto label = it->second;
            if (label != UndefinedSentenceLabel) ret++;
        }
        return ret;
    }
    void ExportResultsToStream(std::ostream &buf) {
        float per = 100.0f / this->TotalSentencesTested();
        buf << "Total:\t" << this->TotalSentencesCorrect() << "\n";
        buf << "Positive correct: " << this->TotalCorrectByLabel(PositiveSentenceLabel) << "\n";
        buf << "Negative correct: " << this->TotalCorrectByLabel(NegativeSentenceLabel) << "\n";
        buf << "Total labels determined: " << this->TotalDefined() << "\n";
        buf << "Proportion of labels determined: " << this->TotalDefined() * per << "%\n";
        buf << "Positive correct: " << this->Percent(this->TotalCorrectByLabel(PositiveSentenceLabel), this->TotalByLabel(PositiveSentenceLabel)) << "% \n";
        buf << "Negative correct: " << this->Percent(this->TotalCorrectByLabel(NegativeSentenceLabel), this->TotalByLabel(NegativeSentenceLabel)) << "% \n";
    }
};

class IEvaluationFramework {
public:
    IEvaluationFramework() {}
    IEvaluationFramework(std::vector<EnumeratedSentence *> *)  {}
    virtual ~IEvaluationFramework() {}
    virtual float Evaluate(IClassifier *c, float *smap, std::vector<EnumeratedSentence *> *s) = 0;
    virtual float Evaluate(IClassifier *, float*) = 0;
};

#endif
