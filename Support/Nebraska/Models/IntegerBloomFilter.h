//
//  IntegerBloomFilter.h
//  Sentiment
//
//  Created by Richard Townsend on 02/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__IntegerBloomFilter__
#define __Sentiment__IntegerBloomFilter__

#include <iostream>
#include <stdint.h>

class IntegerBloomFilter {
private:
    uint64_t bitvec = 0;
public:
    inline void AddItem(uint64_t Item);
    inline bool CheckItem(uint64_t Item);
};

#endif /* defined(__Sentiment__IntegerBloomFilter__) */
