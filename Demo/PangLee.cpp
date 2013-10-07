//
// PangLee.cpp
// Sentiment
//
// Created by Richard Townsend on 07/10/2013.
// Copyright (c) 2013 Richard Townsend. All rights reserved.
//


// C++ headers
#include <vector>
#include <thread>
#include <fstream>
#include <iostream>
// C system headers
#include <signal.h>
#include <stdlib.h>
// Nebraska headers
#include <Evolver.h>
#include <Input/SentiWordNetReader.h>
#include <Input/PLSentenceSource.h>
#include <Models/EnumeratedSentence.h>
#include <Models/Sentence.h>
#include <Models/TokenizedSentence.h>
#include <Models/EnumeratedSentence.h>
#include <Enumerators/HMStringEnumerator.h>
#include <Evaluators/KCrossEvaluator.h>
#include <Classifiers/FFTClassifier.h>
#include <Classifiers/SignMetaClassifier.h>
#include <Classifiers/LengthMetaClassifier.h>
#include <Tokenizers/SentiWordNetTokenizer.h>
#include <Scorers/SentiWordNetScorer.h>
const char * const S_DEFAULT_SWR_PATH = "../Data/SentiWordNet_3.0.0_20120510.txt";
const char * const S_DEFAULT_PL_PATH = "../Data/sentences.csv";
const char * const S_DEFAULT_GENOME_PATH = "best_genome.txt";

volatile int exiting = 0;

void SignalHandler(int sig) {
    exiting = 1;
}

void WorkerThread(std::vector<const EnumeratedSentence *> &etsv, 
		    Evolver &evlv, 
		    size_t genome_size) {

    float *genome = (float *)malloc(genome_size * sizeof(float));
    if (genome == NULL) {
	std::cerr << "Allocation error\n";
	return;
    }
    
    KCrossEvaluator kef (&etsv, 10);
    
    while (!exiting) {
	LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 2> c;
	evlv.BreedGenome(genome);
	float result = kef.Evaluate(&c, genome);
	evlv.PushGenomeFitness(genome, result);
    }
    
    free(genome);
 
}

int main (int argc, const char * argv[]) {
    SentiWordNetReader swr(S_DEFAULT_SWR_PATH);
    SentiWordNetTokenizer swt(swr);
    SentiWordNetScorer scr(swr);
    PLSentenceSource p((char *)S_DEFAULT_PL_PATH) ;
    HMStringEnumerator hms; 
    std::vector<const EnumeratedSentence *> etsv; 
    float *init_scoring_map;
    size_t init_scoring_map_size;
    size_t dont_mutate_beyond;
    float result;
    unsigned int threads; 
    
    // Read in, tokenize sentences
    auto sv = p.GetSentences();
    for (auto it = sv.begin(); it != sv.end(); it++) {
	etsv.push_back(new EnumeratedSentence(new TokenizedSentence(*it, &swt), &hms));
    }
    
    // Create scoring map
    dont_mutate_beyond = hms.GetStrings().size();
    init_scoring_map_size = 0;
    scr.CreateScoringMap(&hms, &init_scoring_map_size, &init_scoring_map);
    init_scoring_map = (float *)calloc(init_scoring_map_size, sizeof(float));
    if (init_scoring_map == NULL) {
	std::cerr << "Allocation error\n";
	return 1;
    }
    scr.CreateScoringMap(&hms, &init_scoring_map_size, &init_scoring_map);
    
    // Compute an initial fitness
    KCrossEvaluator kef(&etsv, 10);
    LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 2> c;
    result = kef.Evaluate(&c, init_scoring_map);
    
    std::cout << "Initial fitness: " << result << "\n";
    
    // Create the evolution environment
    Evolver evlv(init_scoring_map, result, init_scoring_map_size, dont_mutate_beyond, 100); 
    
    // Detect the number of threads in the machine
    threads = std::thread::hardware_concurrency();
    if(!threads) threads = 4;
    std::cout << "Staring " << threads << " worker thread(s)...\n";  
    // Start worker threads
    std::vector<std::thread *> thread_handles; 
    for (int i = 0; i < threads; i++) {
	std::thread *t = new std::thread(WorkerThread, std::ref(etsv), std::ref(evlv),  init_scoring_map_size);
	thread_handles.push_back(t);
    }
    // Wait for all the threads to finish
    for (auto it = thread_handles.begin(); it != thread_handles.end(); it++) {
	(*it)->join();
    }
    
    // Get the best genome and output it
    float *best_genome = evlv.GetMostFitGenome();
    std::ofstream genome_outputf;
    genome_outputf.open(S_DEFAULT_GENOME_PATH, std::ofstream::out | std::ofstream::trunc);
    auto strings = hms.GetStrings();
    for (auto it = strings.begin(); it != strings.end(); it++) {
        auto id = hms.Enumerate(*it);
        auto gn = *(best_genome + id);
        genome_outputf << *it << "\t" << id << "\t" << gn << "\n";
    }
    genome_outputf.close();
}