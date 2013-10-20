//
//  sentence_loader.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "Models/Sentence.h"
#include "PLSentenceSource.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <algorithm>
#include <ctime>

const char * const S_DEFAULT_PL_PATH = "sentences.csv";

//
// PLSentence constructors
//
PLSentenceSource::PLSentenceSource(char *path) {
    PLSentenceSource::init(path);
}

PLSentenceSource::PLSentenceSource() {
    PLSentenceSource::init((char *)S_DEFAULT_PL_PATH);
}

PLSentenceSource::~PLSentenceSource() {
    for(std::vector<Sentence *>::iterator it = this->sentences.begin();
        it != this->sentences.end(); ++it) {
        Sentence *s = *it;
        delete s;
    }
    
}

std::vector<Sentence *> PLSentenceSource::GetSentences() {
    return this->sentences;
}

SentenceReadStatus PLSentenceSource::init(char *path) {
    FILE    *fp;                   // Holds open file handle
    char    *buf;                  // Current line buffer
    size_t  buf_size;
    
    SentenceReadStatus ret;
    
    // Seed random return sort
    std::srand((unsigned int)std::time(0));
    
    // Open the source file
    fp = fopen(path, "r");
    if (fp == NULL) {
        return SentenceReadFileError;
    }
    
    // Read each line from the file
    buf = NULL; buf_size = 0;
    for (buf = NULL, buf_size = 0; getline(&buf, &buf_size, fp);) {
        char *buf_contents[2];
        char *buf_re;
        char *text;
        int label;
        size_t len;
        Sentence *s;
        
        // Split the line at the comma
        buf_contents[0] = strtok_r(buf, ",", &buf_re);
        buf_contents[1] = buf_re;
        
        if (buf_contents[0] == NULL || buf_contents[1] == NULL) break;
        
        // Convert the label to an integer
        if (!sscanf(buf_contents[0], "%d", &label)) {
            // If unsuccessful, say so!
            ret = SentenceReadFormatError;
            goto cleanup;
        }
        
        // Copy the sentence text
        len = strlen(buf_contents[1]) - 3;
        text = (char *)calloc(len, 1);
        if (text == NULL) {
            ret = SentenceReadAllocationError;
            return ret; 
        }
        strncpy(text, buf_contents[1] + 1, len);
        
        // Construct the Sentence object
        s = new Sentence(label, text);
        if (s->GetClassification() == UndefinedSentenceLabel) {
            ret = SentenceReadFormatError;
            goto cleanup;
        }
        free(text);
        this->sentences.push_back(s);
    }
    
    std::random_shuffle(this->sentences.begin(), this->sentences.end());
    
    free(buf);
    ret = SentenceReadOk;
cleanup:
    fclose(fp);
    return ret; 
}