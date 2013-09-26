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
#include "FFTClassifier.h"
#include "SignMetaClassifier.h"
#include "LengthMetaClassifier.h"
#include "math.h"

int main(int argc, const char * argv[])
{

    int positive_correct = 0, positive_counter = 0;
    int negative_correct = 0, negative_counter = 0;
    // WhitespaceTokenizer splits sentences into scorable parts based on
    // whitespace
    WhitespaceTokenizer *wt;
    // PLSentenceSource reads sentences from a CSV file on disk
    PLSentenceSource *p;
    // HMStringEnumerator enumerates GetKey() values from WordTokens
    HMStringEnumerator *hms;
    // Classifier decides whether a sentence is positive or negative
    LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 2> c;
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
    
    // Create a scoring map from SentiWordNet
    scoring_map_size = 0;
    scr.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)calloc(scoring_map_size, sizeof(float));
    if(scoring_map == NULL) {
        std::cerr << "Allocation error";
        return 1;
    }
    scr.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    
    for (auto it = etsv.begin(); it != etsv.end(); it++) {
        c.Train(*it, scoring_map);
    }
    
    // Loop through each sentence and print 
    for(std::vector<EnumeratedSentence *>::iterator it = etsv.begin(); it != etsv.end(); ++it) {
        EnumeratedSentence *s = *it;
        ClassificationLabel l = c.Classify(s, scoring_map);
        ClassificationLabel o = s->GetClassification();
        std::cout << s->GetText() << "\t";
        if (o == PositiveSentenceLabel) {
            positive_counter++;
        }
        else {
            negative_counter++;
        }
        if (l != o) {
            std::cout << "Incorrect\t";
        }
        else {
            if (l == PositiveSentenceLabel) {
                positive_correct++;
            }
            else {
                negative_correct++;
            }
            std::cout << "Correct\t";
        }
        std::cout << s->GetClassification() << "\t" << l << "\t";
        std::cout << 100.0 * positive_correct / fmax(positive_counter, 1) << "\t";
        std::cout << 100.0 * negative_correct / fmax(negative_counter, 1) << "\t";
        std::cout << "\n";
    }
    
    delete p;
    delete wt;
    delete hms;
    
    return 0;
}

