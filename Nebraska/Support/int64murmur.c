//
//  in64murmur.c
//  Sentiment
//
//  Created by Richard Townsend on 02/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include <stdint.h>
#include <stdio.h>

inline uint32_t int64_murmur (uint64_t data, uint32_t seed) {
    // Unrolled version of MurmurHash for bloom filtering
    uint32_t c1 = 0xcc9e2d51;
    uint32_t c2 = 0x1b873593;
    uint32_t r1 = 15;
    uint32_t r2 = 13;
    uint32_t m = 5;
    uint32_t n = 0xe6546b64;
    uint32_t hash = seed;
    uint32_t k;
    
    // Do the first 4-byte chunk of the data
    k = (data & 0xFFFFFFFF00000000) >> 32;
    k *= c1;
    k = (k << r1) | (k >> (32-r1));
    k *= c2;
    hash ^= k;
    hash = (hash << r2) | (hash >> (32-r2));
    hash = hash * m + n;
    
    // Do the second 4-byte chunk of the key
    k = data & 0x00000000FFFFFFFF;
    k *= c1;
    k = (k << r1) | (k >> (32-r1));
    k *= c2;
    hash ^= k;
    hash = (hash << r2) | (hash >> (32-r2));
    hash = hash * m + n;
    
    // No remaining bytes, so skip the next section
    hash ^= 8;
    hash ^= (hash >> 16);
    hash *= 0x85ebca6b;
    hash ^= (hash >> 13);
    hash *= 0xc2b2ae35;
    hash ^= (hash >> 16);
    return hash;
}