//
//  MetaClassifier.h
//  Sentiment
//
//  Created by Richard Townsend on 26/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_MetaClassifier_h
#define Sentiment_MetaClassifier_h

#include <map>
#include "IClassifier.h"

template <class T>
class IMetaClassifier : public IClassifier {
private:
    std::map<unsigned int, T*> classifier_map;
    T* CreateOrReturnClassifier(unsigned int id) {
        T* candidate = this->classifier_map[id];
        if (candidate == NULL) {
            this->classifier_map[id] = new T();
        }
        return this->classifier_map[id];
    }
    virtual unsigned int ComputeClassifierId (EnumeratedSentence *, float *) = 0;
public:
    ~IMetaClassifier() {
        for (auto it = this->classifier_map.begin(); it != this->classifier_map.end(); it++) {
            auto cls = it->second;
            delete cls;
        }
        this->classifier_map.clear();
    }
    void AddToMap(unsigned int id, T *it) {
        this->classifier_map[id] = it;
    }
    ClassificationLabel Classify(EnumeratedSentence *s, float *score_map) {
        unsigned int id = this->ComputeClassifierId(s, score_map);
        this->CreateOrReturnClassifier(id);
        return this->classifier_map[id]->Classify(s, score_map);
    }
    void Train(EnumeratedSentence *s, float *score_map) {
        unsigned int id = this->ComputeClassifierId(s, score_map);
        this->CreateOrReturnClassifier(id);
        return this->classifier_map[id]->Train(s, score_map);
    }
    void Detrain() {
        for (auto it = this->classifier_map.begin(); it != this->classifier_map.end(); it++) {
            auto cls = it->second;
            cls->Detrain();
        }
    }
};

#endif
