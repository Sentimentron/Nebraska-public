//
//  Evolver.cpp
//  Sentiment
//
//  Created by Richard Townsend on 27/09/2013.
//  Copyright (c) 2013 Richard Townsend. All rights reserved.
//
#include <random>
#include <cfloat>
#include "Evolver.h"

const float MUTATION_RATE = 0.25f;

Evolver::~Evolver() {
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto first = it->first;
        free(first);
    }
}

int Evolver::PushGenomeFitness(float *genome, float fitness) {
    float *worst = this->GetLeastFitGenome();
    float worst_fitness = this->fitness_map[worst];
    if (worst_fitness >= fitness) return 0;
    
    // Allocate space for the genome
    float *genome_buf = (float *)malloc(this->genome_size * sizeof(float));
    if (genome_buf == NULL) {
        return 1;
    }
    // Copy over the genome data
    memcpy(genome_buf, genome, this->genome_size * sizeof(float));
    // Increment the number of genomes we have
    this->cur++;
    // Remove the least fit genomes
    for (int i = this->cur; i > this->count; i--) {
        float *cur = this->GetLeastFitGenome();
        if (cur == NULL) break;
        RemoveGenome(cur);
    }
    // Insert the genome into the fitness map
    this->fitness_map[genome_buf] = fitness;
    return 0;
}

void Evolver::RemoveGenome(float *genome) {
    if(!this->fitness_map.erase(genome)) {
        std::cerr << "genome delete failure\n";
    }
    free(genome);
    if (this->cur) this->cur--;
}

float *Evolver::GetLeastFitGenome() {
    float worst_fitness = FLT_MAX;
    float *worst_genome = NULL;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto genome = it->first;
        auto fitness = it->second;
        if (fitness < worst_fitness) {
            worst_genome = genome;
            worst_fitness = fitness;
        }
    }
    return worst_genome;
}

void Evolver::RandomGenome(float *out) {
    for(int i = 0; i < this->genome_size; i++) {
        float *cur = (out + i);
        //if (fabs(*cur) > 0.005) continue;
        *cur = -0.1f + (float)rand()/((float)RAND_MAX/(0.2f));
    }
}

void Evolver::BreedGenome(float *out) {
    float total = 0;
    
    if (this->cur < this->count) {
        // Breed a random genome
        // return this->RandomGenome(out);
    }
    
    // Compute total fitness
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += fitness;
    }
    // Generate a random number between 0 and the total
    float rnd_father = (float)rand()/((float)RAND_MAX/(total));
    float rnd_mother = (float)rand()/((float)RAND_MAX/(total));
    
    // Find the father and the mother
    float *mother, *father;
    total = 0;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += fitness;
        if (total > rnd_father) {
            father = it->first;
            break;
        }
    }
    total = 0;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += fitness;
        if (total > rnd_mother) {
            mother = it->first;
            break;
        }
    }
    
    // Breedin' time!
    for (int i = 0; i < this->genome_size; i++) {
        float *cur = out + i;
        float rnd = (float)rand()/((float)RAND_MAX);
        float rnd2 = (float)rand()/((float)RAND_MAX);
        if (rnd <= 0.5f) {
            // Luke, I am your father!
            *cur = *(father + i);
            if (rnd2 < 0.05f) {
                // Mutation time!
                *cur += -0.01f + (float)rand()/((float)RAND_MAX/(0.02f));
            }
        }
        else {
            // Leia, I am not your father!
            *cur = *(mother + i);
            if (rnd2 < 0.05f) {
                // Mutation time!
                *cur += -0.01f + (float)rand()/((float)RAND_MAX/(0.02f));
            }
        }
    }
}

