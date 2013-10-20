//
//  WordToken.h
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__WordToken__
#define __Sentiment__WordToken__

#include <iostream>
#include <string>

#include "Interfaces/IToken.h"

class WordToken : public IToken {
private:
    std::string word;
public:
    ~WordToken();
    std::string GetKey();
    WordToken(std::string word);
};

#endif /* defined(__Sentiment__WordToken__) */
