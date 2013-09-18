//
//  main.cpp
//  Sentiment
//
//  Created by Richard Townsend on 17/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include <iostream>
#include "HMStringEnumerator.h"
#include "PLSentenceSource.h"
#include "WhitespaceTokenizer.h"
#include "WordToken.h"

int main(int argc, const char * argv[])
{

    // WhitespaceTokenizer splits sentences into scorable parts based on
    // whitespace
    WhitespaceTokenizer *wt;
    // PLSentenceSource reads sentences from a CSV file on disk
    PLSentenceSource *p;
    // HMStringEnumerator enumerates GetKey() values from WordTokens
    HMStringEnumerator *hms;
    // Allows iteration through Sentence objects
    std::vector<Sentence *> sv;
    // Allows iteration thorugh WordTokens
    std::vector<IToken *> tv;
    
    // Construct tokenizer
    wt = new WhitespaceTokenizer();
    hms = new HMStringEnumerator();
    
    // Read sentences from CSV file in the default location
    p = new PLSentenceSource();
    // Iterator sv through the sentences
    sv = p->GetSentences();
    
    // Loop through each sentence and print 
    for(std::vector<Sentence *>::iterator it = sv.begin(); it != sv.end(); ++it) {
        unsigned int en;
        Sentence *s = *it;
        // Print the classification label plus sentence text
        std::cout << s->GetClassificationStr() << " " << s->GetText() << "\n";
        // Tokenize the sentence
        tv = wt->Tokenize(s);
        // Print a new line and then the tokenizer units
        for(std::vector<IToken *>::iterator itt = tv.begin(); itt != tv.end(); ++itt) {
            WordToken *wtn = (WordToken *)*itt;
            std::cout << "\t" << wtn->GetKey();
            en = hms->Enumerate(wtn->GetKey());
            std::cout << "\t" << en << "\n";
        }
    }
    
    delete p;
    delete wt;
    delete hms;
    
    return 0;
}

