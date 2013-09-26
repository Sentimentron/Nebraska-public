//
//  SelfEvaluationFramework.h
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_SelfEvaluationFramework_h
#define Sentiment_SelfEvaluationFramework_h

#include "IClassifier.h"
#include "IEvaluationFramework.h"

class SelfEvaluationFramework : public IEvaluationFramework {
    std::vector<EnumeratedSentence *> *sentences;
public:
    SelfEvaluationFramework() {
        
    }
    SelfEvaluationFramework(std::vector<EnumeratedSentence *> *s) {
        this->sentences = s;
    }
    EvaluationResult Evaluate(IClassifier *c, float *smap, std::vector<EnumeratedSentence *> *s) {
        this->sentences = s;
        return this->Evaluate(c, smap);
    }
    EvaluationResult Evaluate(IClassifier *c, float *smap) {
        EvaluationResult ret;
        // Train the classifier
        for (auto it = this->sentences->begin(); it != this->sentences->end(); it++) {
            c->Train(*it, smap);
        }
        // Evaluate 
        for (auto it = this->sentences->begin(); it != this->sentences->end(); it++) {
            ret.PushResult(*it, c->Classify(*it, smap));
        }
        return ret;
    }
};

#endif
