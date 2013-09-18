//
//  IToken.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef Sentiment_IToken_h
#define Sentiment_IToken_h

#include <string>

class IToken {
public:
    virtual ~IToken() {}
    virtual std::string GetKey() = 0;
};

#endif
