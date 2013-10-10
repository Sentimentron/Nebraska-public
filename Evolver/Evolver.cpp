//
//  Evolver.cpp
//  Sentiment
//
//  Created by Richard Townsend on 10/10/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

// Nebraska headers
#include <Classifiers/FFTClassifier.h>
#include <Classifiers/LengthMetaClassifier.h>
#include <Classifiers/SignMetaClassifier.h>

#include <Enumerators/HMStringEnumerator.h>
#include <Evaluators/KCrossEvaluator.h>

#include <Interfaces/IClassifier.h>
#include <Interfaces/IScorer.h>
#include <Interfaces/ISentenceSource.h>
#include <Interfaces/ITokenizer.h>

#include <Input/PLSentenceSource.h>
#include <Input/SSentenceSource.h>
#include <Input/SentiWordNetReader.h>

#include <Scorers/ExportedGenomeScorer.h>
#include <Scorers/SentiWordNetScorer.h>

#include <Tokenizers/WhitespaceTokenizer.h>
#include <Tokenizers/SentiWordNetTokenizer.h>
#include <Tokenizers/TwitterTokenizer.h>

#include <Evolver.h>

// C++ headers
#include <fstream>
#include <iostream>
#include <thread>
// C headers
#include <signal.h>
#include <string.h>
#include <stdio.h>

volatile int exiting = 0;

void SignalHandler(int sig) {
    exiting = 1;
}

int ProcessScrArgs (int argc, char **argv, int pos, SentiWordNetReader &r, IScorer **s) {
    char *src;
    if (pos >= argc) {
        std::cerr << "Usage: EvolvedGenomeScorer [path]|SentiWordNetScorer\n";
        return 1;
    }
    src = argv[pos];
    if (!strcmp(src, "EvolvedGenomeScorer")) {
        if (pos >= argc-1) {
            std::cerr << "usage: EvolvedGenomeScorer [path]\n";
            return 1;
        }
        char *path = argv[++pos];
        *s = new ExportedGenomeScorer(path);
        return 0;
    }
    else if (!strcmp(src, "SentiWordNetScorer")) {
        *s = new SentiWordNetScorer(r);
        return 0;
    }
    return 1;
}

int ProcessTkArgs (int argc, char **argv, int pos, SentiWordNetReader &r, ITokenizer **t) {
    char *src;
    if (pos >= argc) {
        std::cerr << "Usage: WhiteSpaceTokenizer|SentiWordNetTokenizer|TwitterTokenizer\n";
        return 1;
    }
    src = argv[pos];
    if (!strcmp(src, "WhitespaceTokenizer")) {
        *t = new WhitespaceTokenizer();
        return 0;
    }
    else if (!strcmp(src, "SentiWordNetTokenizer")) {
        *t = new SentiWordNetTokenizer(r);
        return 0;
    }
    else if (!strcmp(src, "TwitterTokenizer")) {
        *t = new TwitterTokenizer(r);
        return 0;
    }
    else {
        std::cerr << "Usage: WhiteSpaceTokenizer|SentiWordNetTokenizer|TwitterTokenizer\n";
        return 1;
    }
}

int ProcessSrcArguments (int argc, char **argv, int pos, ISentenceSource **s) {
    
    char *src, *path;
    
    src = argv[pos];
    if (++pos > argc) {
        std::cerr << "Usage: PLSentenceSource|SSentenceSource path...\n";
        return 1;
    }
    path = argv[pos];
    
    if (!strcmp(src, "PLSentenceSource")) {
        // Reading from Pang Lee, next argument is directory
        *s = new PLSentenceSource(path);
        return 0;
    }
    else if (!strcmp(src, "SSentenceSource")) {
        // Reading from SS
        *s = new SSentenceSource(path);
        return 0;
    }
    else {
        std::cerr << "Usage: PLSentenceSource|SSentenceSource path...\n";
        return 1;
    }
}

int ProcessCmdArguments (int argc, char ** argv,
                         IScorer **s, ISentenceSource **src,
                         ITokenizer **t) {
    
    char *swr_path = NULL;
    SentiWordNetReader *swr;
    
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--src")) {
            if (ProcessSrcArguments(argc, argv, i+1, src)) {
                return 1;
            }
        }
        else if (!strcmp(argv[i], "--swr")) {
            if (i > argc-1) {
                std::cerr << "Usage: --swr [path]\n";
                return 1;
            }
            swr_path = argv[i+1];
            swr = new SentiWordNetReader(swr_path);
        }
        else if (!strcmp(argv[i], "--scorer")) {
            if (swr == NULL) {
                std::cerr << "--swr must be passed before --scorer!\n";
                return 1;
            }
            if (ProcessScrArgs(argc, argv, i+1, *swr, s)) {
                return 1;
            }
        }
        else if (!strcmp(argv[i], "--tokenizer")) {
            if (swr == NULL) {
                std::cerr << "--swr must be passed before --tokenizer!\n";
                return 1;
            }
            if (ProcessTkArgs(argc, argv, i+1, *swr, t)) {
                return 1;
            }
        }
        else { 
            break;
        }
    }
    
    std::cerr << "usage: Evolver --src [args] --scorer [scorer_args] --tokenizer [tk_args]\n";
    return 1;
}

void WorkerThread(std::vector<const EnumeratedSentence *> &etsv,
                  KCrossEvaluator &kef, Evolver &evlv, size_t genome_size) {
    float *genome = (float *)calloc(genome_size, sizeof(float));
    if (genome == NULL) {
        std::cerr << "Allocation error\n";
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

int main (int argc, char ** argv) {
    
    bool allow_evolution    = false;
    IScorer *scorer         = NULL;
    ISentenceSource *source = NULL;
    ITokenizer *tokenizer   = NULL;
    char *export_name = NULL;
    
    std::vector<const EnumeratedSentence *> etsv;
    HMStringEnumerator hms;
    size_t dont_mutate_beyond, scoring_map_size;
    float result;
    unsigned int threads;
    float *scoring_map;
    
    // Process the command arguments
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--evolve")) {
            allow_evolution = true;
        }
        else if (strcmp(argv[i], "--export")) {
            if (i == argc-1) {
                std::cerr << "usage: --export file_name\n";
                return 1;
            }
            export_name = argv[i+1];
        }
    }

    if (ProcessCmdArguments(argc, argv, &scorer, &source, &tokenizer)) {
        return 1;
    }
    if ((scorer == NULL) || (source == NULL) || (tokenizer == NULL)) {
        std::cerr << "Command processing error\n";
        return 1;
    }
    
    // Read in the sentences
    auto sv = source->GetSentences();
    for (auto it = sv.begin(); it != sv.end(); it++) {
        etsv.push_back(new EnumeratedSentence(new TokenizedSentence(*it, tokenizer), &hms));
    }
    
    // 
    // Work out the base-line performance
    
    // Create scoring map
    dont_mutate_beyond = hms.GetStrings().size();
    scoring_map_size = 0; scoring_map = NULL;
    scorer->CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    scoring_map = (float *)calloc(scoring_map_size, sizeof(float));
    if (scoring_map == NULL) {
        std::cerr << "Allocation error\n";
        return 1;
    }
    scorer->CreateScoringMap(&hms, &scoring_map_size, &scoring_map);
    
    // Create cross-evaluator, compute fitness
    KCrossEvaluator kef(&etsv, 5); // TODO: allow customization of folds/technique
    LengthMetaClassifier<SignMetaClassifier<FFTClassifier>, 1> c;
    result = kef.Evaluate(&c, scoring_map);
    std::cout << "Initial fitness: " << result << "\n";
    if (!allow_evolution) return 0;
    
    // Create the evolution environment
    Evolver evlv(scoring_map, result, scoring_map_size, dont_mutate_beyond, 100); // TODO: allow genome number to be customized
    
    // Install signal handler
    signal(SIGINT, SignalHandler);
    
    // Create worker threads
    threads = 4;
    std::cout << "Starting " << threads << " worker thread(s)...\n";
    std::vector<std::thread *> thread_handles;
    for (int i = 0; i < threads; i++) {
        std::thread *t = new std::thread(WorkerThread, std::ref(etsv), std::ref(kef), std::ref(evlv), scoring_map_size);
        thread_handles.push_back(t);
    }
    
    // Wait for the worker threads to terminate
    for (auto it = thread_handles.begin(); it != thread_handles.end(); it++) {
        (*it)->join();
    }
    
    // If output specified, output the genome
    if(export_name == NULL) return 0;
    float *best_genome = evlv.GetMostFitGenome();
    std::ofstream genome_outputf;
    genome_outputf.open(export_name, std::ofstream::out | std::ofstream::trunc);
    auto strings = hms.GetStrings();
    for (auto it = strings.begin(); it != strings.end(); it++) {
        auto id = hms.Enumerate(*it);
        auto gn = *(best_genome + id);
        genome_outputf << *it << "\t" << id << "\t" << gn << "\n";
    }
    genome_outputf.close();
}