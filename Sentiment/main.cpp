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
#include "SentiWordScorer.h"
#include "TokenizedSentence.h"
#include "EnumeratedSentence.h"

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
    std::vector<TokenizedSentence *>tsv;
    std::vector<EnumeratedSentence *> etsv;
    // Allows iteration thorugh WordTokens
    std::vector<IToken *> tv;
    // SentiWordScorer retrieves word scores from SentiWordNet
    SentiWordScorer scr;
    float *scoring_map;
    size_t scoring_map_size; 
    // Construct tokenizer
    wt = new WhitespaceTokenizer();
    hms = new HMStringEnumerator();
    
    // Read sentences from CSV file in the default location
    p = new PLSentenceSource();
    // Iterator sv through the sentences
    sv = p->GetSentences();
    
    // Create a scoring map from SentiWordNet
    scoring_map_size = 0;
    scr.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)malloc(scoring_map_size * sizeof(float));
    if(scoring_map == NULL) {
        std::cerr << "Allocation error";
        return 1;
    }
    scr.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    
    // Create a vector of tokenized sentences 
    for(std::vector<Sentence *>::const_iterator it = sv.begin();
        it != sv.end(); it++) {
        tsv.push_back(new TokenizedSentence(*it, wt));
    }
    
    // Create a vector of enumerated sentences
    for (std::vector<TokenizedSentence *>::const_iterator it = tsv.begin();
         it != tsv.end(); it++) {
        etsv.push_back(new EnumeratedSentence(*it, hms));
    }
    
    // Loop through each sentence and print 
    for(std::vector<EnumeratedSentence *>::iterator it = etsv.begin(); it != etsv.end(); ++it) {
        unsigned int en;
        EnumeratedSentence *st = *it;
        std::vector<IToken *> tv = st->GetParent()->GetTokens();
        // Print the classification label plus sentence text
        std::cout << st->GetClassificationStr() << " " << st->GetText() << "\n";
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

