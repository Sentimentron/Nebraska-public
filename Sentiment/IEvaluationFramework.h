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

class EvaluationResult {
private:
    std::map<EnumeratedSentence *, ClassificationLabel> results;
public:
    void PushResult(EnumeratedSentence *s, ClassificationLabel l) {
        this->results[s] = l;
    }
    unsigned int TotalSentencesTrained;
    unsigned int TotalSentencesTested() {
        return (unsigned int)results.size();
    }
    unsigned int TotalSentencesCorrect() {
        unsigned int ret = 0;
        for(auto it = this->results.begin(); it != this->results.end(); it++) {
            auto sentence = it->first;
            auto label = it->second;
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
};

class IEvaluationFramework {
public:
    IEvaluationFramework() {}
    IEvaluationFramework(std::vector<EnumeratedSentence *> *)  {}
    virtual ~IEvaluationFramework() {}
    virtual EvaluationResult Evaluate(IClassifier *, float*) = 0;
};

#endif
