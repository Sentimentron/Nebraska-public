//
//  FloatingFloatBuffer.h
//  Sentiment
//
//  Created by Richard Townsend on 22/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__FloatingFloatBuffer__
#define __Sentiment__FloatingFloatBuffer__

#include <iostream>

#include <vector>

class FloatingFloatBuffer {
private:
    float *items;
    unsigned int length;
    unsigned int offset = 0;
    float mean;
    float variance;
    bool mean_calculated = false;
    bool variance_calculated = false; 
public:
    FloatingFloatBuffer(float *data, unsigned int length) {
        this->items = data;
        this->length = length;
        this->offset = 0;
    }
    void SetStartOffset(unsigned int offset) {
        this->offset = offset;
    }
    unsigned int GetLength() {
        return this->length;
    }
    float ComputeMean() {
        if (this->mean_calculated) return this->mean;
        unsigned int length = this->GetLength();
        float ret = 0.0f;
        for (int i = 0; i < this->length; i++) {
            ret += *(this->items + i);
        }
        this->mean_calculated = true;
        this->mean = ret / length;
        return this->mean;
    }
    float ComputeVariance() {
        if (this->variance_calculated) return this->variance; 
        unsigned int length = this->GetLength();
        float mean = this->ComputeMean();
        float ret = 0.0f;
        for (int i = 0; i < this->length; i++) {
            float cur = *(this->items + i);
            cur -= mean;
            ret += cur * cur;
        }
        this->variance = ret / length;
        this->variance_calculated = true;
        return this->variance;
    }
    inline float operator [] (int offset) {
        int vec_offset;
        // Case 1: something before the start of the offset
        if(offset < this->offset) {
            return 0.0f;
        }
        // Case 2: something after the signal
        if(offset >= this->offset + this->length) {
            return 0.0f;
        }
        // Case 3: Have to compute true offset
        vec_offset = offset - this->offset;
        return this->items[vec_offset];
    }
};

#endif /* defined(__Sentiment__FloatingFloatBuffer__) */
