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

class Evolver {
private:
    // Associates each genome with a fitness value
    std::map<float *, float> fitness_map;
    size_t genome_size;
    // Stores the number of genomes which are allowed
    unsigned int count;
    // Stores the number of genomes currently managed
    unsigned int cur = 0;
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
    unsigned int run = 0;
    bool output = false;
    int _PushGenomeFitness(const float *, float);
    inline float Random(const float min, const float max) {
        return -min + (float)rand()/((float)RAND_MAX/(max-min));
    }
public:
    // Breeds a new genome, places the result in float
    void BreedGenome(float *);
    // Copies the first argument, stores fitness value
    int PushGenomeFitness(const float *, float);
    ~Evolver();
    Evolver(float *init, float fitness, size_t size, unsigned int count) {
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
