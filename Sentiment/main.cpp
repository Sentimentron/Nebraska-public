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
#include "SentiWordNetReader.h"
#include "Evolver.h"
#include "math.h"

int exiting = 0;

void WorkerThread(const KCrossEvaluator &kef, const std::vector<const EnumeratedSentence *> &etsv,
                  Evolver &evlv, size_t genome_size) {
    float *genome = (float *)malloc(genome_size * sizeof(float));
    if (genome == NULL) {
        std::cerr << "Allocation error!\n";
        return;
    }
    
    while (!exiting) {
        LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 1> c;
        evlv.BreedGenome(genome);
        float result = kef.Evaluate(&c, genome);
        evlv.PushGenomeFitness(genome, result);
    }
    
    free(genome);
}

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
    
    // Evaluate the classifier
    std::cout << "Self evaluation: \n";
    //float s = sef.Evaluate(&c, scoring_map, &etsv);
    //std::cout << s;
    std::cout << "\nk-fold validation (k = 3):\n";
    int run_count = 0, best_run = 0;
    float best_accuracy = 0;
    // Evaluate the classifier using cross-fold
    float *smap = (float *)malloc(scoring_map_size * sizeof(float));
    if (smap == NULL) {
        std::cerr << "Allocation failure!\n";
        return 1;
    }
    
    // Create the Evolution environment
    KCrossEvaluator kef(&etsv, 5);
    float result = kef.Evaluate(&c, scoring_map);
    Evolver evlv(scoring_map, result, scoring_map_size, 200);
    
    WorkerThread(kef, etsv, evlv, scoring_map_size);
    
    while(1) {
        run_count++;
        LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 1> *c2 = new LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 1>();
        evlv.BreedGenome(smap);
        float result = kef.Evaluate(c2, smap);
        std::cout << "#(" << run_count << ") Current fitness: " << result << "\n";
        std::cout << "Best fitness: " << best_accuracy << "(Run #" << best_run << ")\n";
        if(result > best_accuracy) {
            best_run = run_count;
            best_accuracy = result;
        }
        evlv.PushGenomeFitness(smap, result);
        delete c2;
    }
    
    delete p;
    delete wt;
    delete hms;
    
    for (auto it = etsv.begin(); it != etsv.end(); it++) {
        delete *it;
    }
    
    free(scoring_map);
    free(smap);
    return 0;
}

