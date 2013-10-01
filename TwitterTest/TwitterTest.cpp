//
//  TwitterTest.cpp
//  Sentiment
//
//  Created by Richard Townsend on 01/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#include "FFTClassifier.h"
#include "SentiWordTokenizer.h"
#include "PLSentenceSource.h"
#include "HMStringEnumerator.h"
#include "LengthMetaClassifier.h"
#include "SignMetaClassifier.h"
#include "SentiWordNetReader.h"
#include "SentiWordScorer.h"
#include "SSentenceSource.h"
#include "EnumeratedSentence.h"
#include "KCrossEvaluator.h"
#include "ExportedGenomeScorer.h"

#include <stdio.h>

const char * const S_DEFAULT_TWITTER_PATH = "twitter.csv";
const char * const S_DEFAULT_GENOME_PATH  = "best_genome.txt";

int main (int argc, const char * argv[]) {
    SentiWordTokenizer wt;
    PLSentenceSource psrc;
    HMStringEnumerator hms;
    FFTClassifier c;
    //LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 2> c;
    SentiwordNetReader swr;
    SSentenceSource ssrc(S_DEFAULT_TWITTER_PATH);
    SentiWordScorer scr(swr);
    std::vector<Sentence *>sv;
    std::vector<const EnumeratedSentence *> etsv;
    float *scoring_map;
    size_t scoring_map_size; 
    
    // Read in the sentences
    sv = ssrc.GetSentences();
    // Convert to enumerated sentences
    for (auto it = sv.begin(); it != sv.end(); it++) {
        etsv.push_back(new EnumeratedSentence(new TokenizedSentence(*it, &wt), &hms));
    }
    
    // Create a scoring map from SentiWordNet
    scoring_map_size = 0; scoring_map = NULL;
    scr.CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)calloc(scoring_map_size, sizeof(float));
    if (scoring_map == NULL) {
        std::cerr << "Allocation error\n";
        return 1;
    }
    scr.CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    
    // Evaluate 
    KCrossEvaluator kef(&etsv, 5);
    float result = kef.Evaluate(&c, scoring_map);
    std::cout << "Baseline accuracy: " << result << "%\n";
    
    // Load in the improved genome
    ExportedGenomeScorer egs(S_DEFAULT_GENOME_PATH);
    free(scoring_map); scoring_map = NULL; scoring_map_size = 0;
    egs.CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)calloc(scoring_map_size, sizeof(float));
    if (scoring_map == NULL) {
        std::cerr << "Allocation error\n";
        return 1;
    }
    scr.CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    
    result = kef.Evaluate(&c, scoring_map);
    std::cout << "Evolved accuracy: " << result << "%\n";
    return 0;
}