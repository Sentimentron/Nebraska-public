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
#include "IEvaluationFramework.h"

/*    IEvaluationFramework() {}
 IEvaluationFramework(std::vector<EnumeratedSentence *> *)  {}
 virtual ~IEvaluationFramework() {}
 virtual EvaluationResult Evaluate(IClassifier *c, float *smap, std::vector<EnumeratedSentence *> *s) = 0;
 virtual EvaluationResult Evaluate(IClassifier *, float*) = 0;*/

class KCrossEvaluator : IEvaluationFramework {
private:
    void GenerateRandomizedFolds(std::vector<EnumeratedSentence *>*s);
    //std::vector<std::vector<EnumeratedSentence *>> folds;
    std::map<unsigned int, std::vector<EnumeratedSentence *>> folds;
    EvaluationResult EvaluateConfiguration(IClassifier *, float *,
                                           std::vector<std::vector<EnumeratedSentence *>> ,
                                           std::vector<EnumeratedSentence *>
                                           );
    unsigned int number_of_folds = 3;
public:
    KCrossEvaluator() {};
    KCrossEvaluator(unsigned int folds) {
        this->number_of_folds = folds;
    }
    KCrossEvaluator(std::vector<EnumeratedSentence *> *s) {
        this->GenerateRandomizedFolds(s);
    }
    KCrossEvaluator(std::vector<EnumeratedSentence *> *s, unsigned int folds) {
        this->number_of_folds = folds;
    }
    EvaluationResult Evaluate(IClassifier *c, float *smap, std::vector<EnumeratedSentence *> *s) {
        this->GenerateRandomizedFolds(s);
        return this->Evaluate(c, smap);
    }
    EvaluationResult Evaluate(IClassifier *, float*);
};

#endif /* defined(__Sentiment__KCrossEvaluator__) */
