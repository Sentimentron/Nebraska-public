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
#include "WordToken.h"
#include "SentiWordScorer.h"
#include "TokenizedSentence.h"
#include "EnumeratedSentence.h"
#include "FFTClassifier.h"
#include "SignMetaClassifier.h"
#include "LengthMetaClassifier.h"
#include "SelfEvaluationFramework.h"
#include "KCrossEvaluator.h"
#include "SentiWordTokenizer.h"
#include "math.h"

int main(int argc, const char * argv[])
{
    // WhitespaceTokenizer splits sentences into scorable parts based on
    // whitespace
    SentiWordTokenizer *wt;
    // PLSentenceSource reads sentences from a CSV file on disk
    PLSentenceSource *p;
    // HMStringEnumerator enumerates GetKey() values from WordTokens
    HMStringEnumerator *hms;
    // Classifier decides whether a sentence is positive or negative
    LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 2> c;
    // SelfEvaluationFramework evaluates the classifier
    SelfEvaluationFramework sef;
    KCrossEvaluator kef(20);
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
    wt = new SentiWordTokenizer();
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
    
    // Evaluate the classifier
    std::cout << "Self evaluation: \n";
    EvaluationResult s = sef.Evaluate(&c, scoring_map, &etsv);
    s.ExportResultsToStream(std::cout);
    std::cout << "\nk-fold validation (k = 3):\n";
    // Evaluate the classifier using cross-fold
    EvaluationResult k = kef.Evaluate(&c, scoring_map, &etsv);
    
    delete p;
    delete wt;
    delete hms;
    
    return 0;
}

