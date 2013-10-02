//
//  IntegerBloomFilter.cpp
//  Sentiment
//
//  Created by Richard Townsend on 02/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "IntegerBloomFilter.h"

uint32_t int64_murmur (uint64_t data, uint32_t seed);

const uint64_t S_DEFAULT_HASH_1 = 0x9ecb9021;
const uint64_t S_DEFAULT_HASH_2 = 0x811c761b;

void IntegerBloomFilter::AddItem(uint64_t item) {
    uint32_t h1, h2;
    h1 = int64_murmur(item, S_DEFAULT_HASH_1) % 64;
    h2 = int64_murmur(item, S_DEFAULT_HASH_2) % 64;
    this->bitvec |= (1 << h1) | (1 << h2);
}

bool IntegerBloomFilter::CheckItem(uint64_t item) {
    uint32_t h1, h2;
    h1 = int64_murmur(item, S_DEFAULT_HASH_1) % 64;
    h2 = int64_murmur(item, S_DEFAULT_HASH_2) % 64;
    return this->bitvec & ((1 << h1) | (1 << h2));
}