//
//  SentiWordNetReader.h
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__SentiWordNetReader__
#define __Sentiment__SentiWordNetReader__

#include <vector>
#include <iostream>
#include <string>

const char * const S_DEFAULT_SENTIWORDNET_PATH = "SentiWordNet_3.0.0_20120510.txt";

class SentiwordNetReader {
private:
    std::string path;
    std::vector<std::vector<std::string>> contents;
    void init();
public:
    std::vector<std::vector<std::string>> GetContents() {
        return this->contents;
    }
    SentiwordNetReader() {
        this->path = S_DEFAULT_SENTIWORDNET_PATH;
        this->init();
    }
    SentiwordNetReader(std::string path) {
        this->path = path;
        this->init();
    }
}; 

#endif /* defined(__Sentiment__SentiWordNetReader__) */
