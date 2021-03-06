//
//  KCrossEvaluator.h
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__KCrossEvaluator__
#define __Sentiment__KCrossEvaluator__

#include <iostream>
#include "Interfaces/IEvaluationFramework.h"

class KCrossEvaluator : IEvaluationFramework {
private:
    void GenerateRandomizedFolds(std::vector<const EnumeratedSentence *>*s);
    //std::vector<std::vector<EnumeratedSentence *>> folds;
    std::map<unsigned int, std::vector<const EnumeratedSentence *>> folds;
    const EvaluationResult EvaluateConfiguration(IClassifier *, float *,
                                           std::vector<std::vector<const EnumeratedSentence *>> ,
                                           std::vector<const EnumeratedSentence *>
                                           ) const;
    unsigned int number_of_folds;
    
    const std::map<unsigned int, std::vector<const EnumeratedSentence *>> GetFolds() const {
        return this->folds;
    }
    void Construct() {
	this->number_of_folds = 3;
    }
public:
    KCrossEvaluator() {
	this->Construct();
    }
    KCrossEvaluator(unsigned int folds) {
        this->number_of_folds = folds;
    }
    KCrossEvaluator(std::vector<const EnumeratedSentence *> *s) {
	this->Construct();
        this->GenerateRandomizedFolds(s);
    }
    KCrossEvaluator(std::vector<const EnumeratedSentence *> *s, unsigned int folds) {
        this->number_of_folds = folds;
        this->GenerateRandomizedFolds(s);
    }
    float Evaluate(IClassifier *c, float *smap, std::vector<const EnumeratedSentence *> *s) {
        this->GenerateRandomizedFolds(s);
        return this->Evaluate(c, smap);
    }
    const float Evaluate(IClassifier *, float*) const;
};

#endif /* defined(__Sentiment__KCrossEvaluator__) */
