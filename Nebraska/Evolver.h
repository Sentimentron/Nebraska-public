//
//  Evolver.h
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__Evolver__
#define __Sentiment__Evolver__

#include <pthread.h>
#include <iostream>
#include <map>
#include <vector>
#include "sfmt.h"
#include <time.h>

/*const float MUTATION_RATE = 0.0025f;
 const float MUTATION_AMOUNT = 0.0025f;
 const float FITNESS_PREF = 3.5f;*/

class Evolver {
private:
    // Associates each genome with a fitness value
    std::map<float *, float> fitness_map;
    size_t genome_size;
    // Stores the number of genomes which are allowed
    unsigned int count;
    // Stores the number of genomes currently managed
    unsigned int cur;
    // Removes the genome from the map, frees it
    void RemoveGenome(float *);
    // Returns the least-fit genome
    float *GetLeastFitGenome();
    void RandomGenome(float *);
    void ComputeStats();
    float GetTotalFitness();
    float *ChooseParentFromFitnessMap(float);
    float *ChooseRandomParent(float);
    float best_fitness;
    unsigned int best_run;
    float average_fitness;
    std::pair<float *, float *> ChooseParents();
    pthread_mutex_t runlock;
    pthread_mutex_t maplock;
    unsigned int run;
    bool output;
    int _PushGenomeFitness(const float *, float);
    float mutation_rate;
    float mutation_amount;
    float fitness_pref;
    inline float Random(const float min, const float max) {
        double rnd = this->smft.Random();
        rnd *= (max-min);
        return min + rnd;
    }
    const size_t dont_mutate_beyond;
    CRandomSFMT0 smft;
    void Construct() {
	this->cur = 0;
	this->best_fitness = 0.0f;
	this->average_fitness = 0.0f;
	this->best_run = 0;
	this->run = 0;
	this->mutation_rate = 0.05f;
	this->mutation_amount = 0.025f;
	this->fitness_pref = 3.5f;
	this->output = false;
    }
public:
    // Breeds a new genome, places the result in float
    void BreedGenome(float *);
    // Copies the first argument, stores fitness value
    int PushGenomeFitness(const float *, float);
    float *GetMostFitGenome();
    ~Evolver();
    Evolver(float *init, float fitness, size_t size, size_t dont_mutate_beyond, unsigned int count) : smft((int)time(NULL)), dont_mutate_beyond(dont_mutate_beyond) {
	this->Construct();
        this->genome_size = size;
        this->count = count;
        pthread_mutex_init(&this->runlock, NULL);
        pthread_mutex_init(&this->maplock, NULL);
        for (int i = 0; i < count; i++) {
            this->_PushGenomeFitness(init, fitness);
        }
        this->run = 0;
        this->output = true;
    }
};

#endif /* defined(__Sentiment__Evolver__) */
