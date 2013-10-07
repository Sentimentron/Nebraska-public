//
//  HMStringEnumerator.h
//  Sentiment
//
//  Created by Richard Townsend on 18/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__HMStringEnumerator__
#define __Sentiment__HMStringEnumerator__

#include <map>
#include <string>
#include <unordered_map>
#include <vector> 

#include <iostream>
#include "Interfaces/IStringEnumerator.h"

class HMStringEnumerator : public IStringEnumerator {
private:
    std::unordered_map<std::string, unsigned int>   forward_map;
    std::vector<std::string>                        reverse_map;
    unsigned int                                    identifier;
public:
    ~HMStringEnumerator();
    HMStringEnumerator();
    const std::vector<std::string> GetStrings() const {
        return this->reverse_map;
    }
    unsigned int Enumerate(std::string);
    unsigned int GetSize();
};

#endif /* defined(__Sentiment__HMStringEnumerator__) */
