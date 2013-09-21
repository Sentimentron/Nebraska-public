//
//  IStringEnumerator.h
//  Sentiment
//
//  Created by Richard Townsend on 18/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_IStringEnumerator_h
#define Sentiment_IStringEnumerator_h

#include <string>

class IStringEnumerator {
public:
    virtual ~IStringEnumerator() {}
    virtual unsigned int Enumerate(std::string) = 0;
    virtual unsigned int GetSize() = 0;
};


#endif
