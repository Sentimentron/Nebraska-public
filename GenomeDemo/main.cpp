//
//  main.cpp
//  GenomeDemo
//
//  Created by Richard Townsend on 30/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "SentiWordNetReader.h"
#include "FFTClassifier.h"
#include "SignMetaClassifier.h"
#include "LengthMetaClassifier.h"
#include "SentiWordNetReader.h"
#include "PLSentenceSource.h"
#include "SentiWordTokenizer.h"
#include "HMStringEnumerator.h"
#include "SentiWordScorer.h"
#include "KCrossEvaluator.h"
#include "ExportedGenomeScorer.h"

#include <iostream>

const char * S_DEFAULT_GENOME_PATH = "/Users/rtownsend/best_genome.txt";

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
    //  SelfEvaluationFramework sef;
    SentiwordNetReader swr;
    // Allows iteration through Sentence objects
    std::vector<Sentence *> sv;
    std::vector<TokenizedSentence *>tsv;
    std::vector<const EnumeratedSentence *> etsv;
    // Allows iteration thorugh WordTokens
    std::vector<IToken *> tv;
    // SentiWordScorer retrieves word scores from SentiWordNet
    SentiWordScorer scr(swr);
    float *scoring_map;
    size_t scoring_map_size;
    // Construct tokenizer
    wt = new SentiWordTokenizer(swr);
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
    
    KCrossEvaluator kef(&etsv, 5);
    float result = kef.Evaluate(&c, scoring_map);
    
    std::cout << "SentiWordNet accuracy under k = 5-cross validation: " << result << "\n";
    
    // Load in the improved genome
    ExportedGenomeScorer egs(S_DEFAULT_GENOME_PATH);
    free(scoring_map); scoring_map = NULL;
    egs.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)calloc(scoring_map_size, sizeof(float));
    if(scoring_map == NULL) {
        std::cerr << "Allocation error";
        return 1;
    }
    egs.CreateScoringMap(hms, &scoring_map_size, &scoring_map);
    
    result = kef.Evaluate(&c, scoring_map);
    std::cout << "Evolved genome accuracy under k = 5-cross validation: " << result << "\n";
    
    return 0;
}

