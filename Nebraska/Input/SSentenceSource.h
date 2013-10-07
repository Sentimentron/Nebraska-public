//
//  SanalyticsReader.h
//  Sentiment
//
//  Created by Richard Townsend on 01/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__SanalyticsReader__
#define __Sentiment__SanalyticsReader__

#include <vector>
#include <string>
#include <iostream>

#include "Interfaces/ISentenceSource.h"
#include "Models/Sentence.h"

class SSentenceSource : ISentenceSource {
private:
    std::vector<Sentence *> sentences;
public:
    std::vector<Sentence *> GetSentences() {
        return this->sentences; 
    }
    SSentenceSource(std::string path);
};

#endif /* defined(__Sentiment__SanalyticsReader__) */
