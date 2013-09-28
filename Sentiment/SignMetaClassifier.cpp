//
//  SignMetaClassifier.cpp
//  Sentiment
//
//  Created by Richard Townsend on 25/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//


#include "SignMetaClassifier.h"
#include "math.h"
#include "inttypes.h"
int sign_count(const EnumeratedSentence *s, float *smap) {
    auto vec = s->GetEnumeratedVector();
    bool last = 0.0f;
    int ret = 0;
    for(auto it = vec.begin(); it != vec.end(); it++) {
        float score = *(smap + *it);
        if (fabs(score) < 0.005) continue;
        if (fabs(last) < 0.005) {
            last = score;
            continue;
        }
        if (last < 0 && score < 0) {
            continue;
        }
        if (last > 0 && score > 0) {
            continue;
        }
        last = score;
        ret++;
    }
    return ret;
}