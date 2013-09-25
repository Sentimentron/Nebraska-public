//
//  SignMetaClassifier.h
//  Sentiment
//
//  Created by Richard Townsend on 25/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__SignMetaClassifier__
#define __Sentiment__SignMetaClassifier__

#include <iostream>
#include "IClassifier.h"
#include <map>

int sign_count(EnumeratedSentence *s, float *smap);

template <class T>
class SignMetaClassifier : public IClassifier {
private:
    std::map<unsigned int, T*> classifier_map;
    T* CreateOrReturnClassifier(unsigned int id) {
        T* candidate = this->classifier_map[id];
        if (candidate == NULL) {
            this->classifier_map[id] = new T();
        }
        return this->classifier_map[id];
    }
public:
    void AddToMap(unsigned int id, T *it) {
        this->classifier_map[id] = it;
    }
    ClassificationLabel Classify(EnumeratedSentence *s, float *score_map) {
        unsigned int id = sign_count(s, score_map);
        this->CreateOrReturnClassifier(id);
        return this->classifier_map[id]->Classify(s, score_map);
    }
    void Train(EnumeratedSentence *s, float *score_map) {
        unsigned int id = sign_count(s, score_map);
        this->CreateOrReturnClassifier(id);
        return this->classifier_map[id]->Train(s, score_map);
    }
};

#endif /* defined(__Sentiment__SignMetaClassifier__) */
