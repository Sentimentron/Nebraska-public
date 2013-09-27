//
//  KCrossEvaluator.cpp
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "KCrossEvaluator.h"
#include <random>
#include <algorithm>

void KCrossEvaluator::GenerateRandomizedFolds(std::vector<EnumeratedSentence *> *s) {
    std::vector<EnumeratedSentence *> tmp;
    // Copy the source vector into tmp
    for (auto it = s->begin(); it != s->end(); it++) tmp.push_back(*it);
    // Randomize tmp
    std::random_shuffle(tmp.begin(), tmp.end());
    // Generate things into folds
    int fold_index = 0;
    for(auto it = tmp.begin(); it != tmp.end(); it++) {
        this->folds[fold_index].push_back(*it);
        // Choose the next fold
        fold_index++;
        fold_index %= this->number_of_folds;
    }
}

EvaluationResult KCrossEvaluator::EvaluateConfiguration(IClassifier *c, float *smap,
                                                           std::vector<std::vector<EnumeratedSentence *>> training,
                                                           std::vector<EnumeratedSentence *> testing
                                                           ) {
    EvaluationResult ret; 
    // Detrain the classifier
    c->Detrain();
    // Train the classifier on each training fold
    for (auto train_it = training.begin(); train_it != training.end(); train_it++) {
        for (auto it = train_it->begin(); it != train_it->end(); it++) {
            // Train the classifier on each sentence within each training fold
            c->Train(*it, smap);
        }
    }
    // Evaluate the classifier
    for (auto it = testing.begin(); it != testing.end(); it++) {
        ret.PushResult(*it, c->Classify(*it, smap));
    }
    return ret;
}

EvaluationResult KCrossEvaluator::Evaluate(IClassifier *c, float *smap) {
    std::vector<std::vector<EnumeratedSentence *>> training;
    std::vector<EnumeratedSentence *> testing;
    std::vector<EvaluationResult> results;
    for (int i = 0; i < this->number_of_folds; i++) {
        // Empty everything so far
        training.clear();
        // At any point, fold i is the one used for testing
        testing = this->folds[i];
        for (int j = 0; j < this->number_of_folds; j++) {
            // Folds j represent those used for training
            if (i == j) continue;
            training.push_back(this->folds[j]);
        }
        results.push_back(this->EvaluateConfiguration(c, smap, training, testing));
    }
    for (auto it = results.begin(); it != results.end(); it++) {
        it->ExportResultsToStream(std::cout);
    }
    return results[0];
}

