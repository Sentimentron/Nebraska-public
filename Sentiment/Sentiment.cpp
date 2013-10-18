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
#include "SSentenceSource.h"
#include "TwitterTokenizer.h"
#include "Evolver.h"
#include "math.h"
#include "ExportedGenomeScorer.h"   
#include "TwitterTokenizer.h"
#include <signal.h>
#include <thread>
#include <fstream>

const char * const S_DEFAULT_TWITTER_PATH = "twitter.csv";
const char * const S_DEFAULT_GENOME_PATH  = "best_genome_twitter.txt";

volatile int exiting = 0;

void SignalHandler(int sig) {
    exiting = 1;
}

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
    TwitterTokenizer *wt;
    // PLSentenceSource reads sentences from a CSV file on disk
    SSentenceSource *p;
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
    // SentiWordScorer scr(swr);
    ExportedGenomeScorer scr("best_genome.txt");
    float *scoring_map;
    size_t scoring_map_size;
    size_t dont_mutate_beyond;
    // Construct tokenizer
    wt = new TwitterTokenizer(swr);
    hms = new HMStringEnumerator();
    
    // Read sentences from CSV file in the default location
    p = new SSentenceSource(S_DEFAULT_TWITTER_PATH);
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
    
    dont_mutate_beyond = hms->GetStrings().size();
    
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
    // Evaluate the classifier using cross-fold
    float *smap = (float *)malloc(scoring_map_size * sizeof(float));
    if (smap == NULL) {
        std::cerr << "Allocation failure!\n";
        return 1;
    }
    
    // Create the Evolution environment
    KCrossEvaluator kef(&etsv, 5);
    float result = kef.Evaluate(&c, scoring_map);
    Evolver evlv(scoring_map, result, scoring_map_size, dont_mutate_beyond, 100);
    
    // Set up Ctrl+C handling
    signal(SIGINT, SignalHandler);
    
    // Get the number of cores in the machine
    unsigned int threads = std::thread::hardware_concurrency();
    std::vector<std::thread *> thread_handles;
    // Start worker threads
    for (int i = 0; i < threads; i++) {
        std::thread *t = new std::thread(WorkerThread, std::ref(kef), std::ref(etsv), std::ref(evlv), scoring_map_size);
        thread_handles.push_back(t);
    }
    // Wait for worker threads to respond to signal
    for (auto it = thread_handles.begin(); it != thread_handles.end(); it++) {
        (*it)->join();
    }
    
    // Get the best genome
    float *best_genome = evlv.GetMostFitGenome();
    
    // Output the best genome
    std::ofstream genome_outputf;
    genome_outputf.open(S_DEFAULT_GENOME_PATH, std::ofstream::out | std::ofstream::trunc);
    auto strings = hms->GetStrings();
    for (auto it = strings.begin(); it != strings.end(); it++) {
        auto id = hms->Enumerate(*it);
        auto gn = *(best_genome + id);
        genome_outputf << *it << "\t" << id << "\t" << gn << "\n";
    }
    genome_outputf.close();

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
