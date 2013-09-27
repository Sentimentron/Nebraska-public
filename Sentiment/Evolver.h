//
//  Evolver.h
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//

#ifndef __Sentiment__Evolver__
#define __Sentiment__Evolver__

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
public:
    // Breeds a new genome, places the result in float
    void BreedGenome(float *);
    // Copies the first argument, stores fitness value
    int PushGenomeFitness(float *, float);
    ~Evolver();
    Evolver(float *init, float fitness, size_t size, unsigned int count) {
        this->genome_size = size;
        this->count = count;
        this->PushGenomeFitness(init, fitness);
    }
};

#endif /* defined(__Sentiment__Evolver__) */
