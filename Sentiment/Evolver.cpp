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

const float MUTATION_RATE = 0.15f;
const float MUTATION_AMOUNT = 0.005f;
const float FITNESS_PREF = 3.5f;

Evolver::~Evolver() {
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto first = it->first;
        free(first);
    }
}

int Evolver::PushGenomeFitness(float *genome, float fitness) {
    
    pthread_mutex_lock(&this->runlock);
    this->run++;
    if (this->output) {
        std::cout << "#(" << this->run << ") Current fitness: " << fitness << "\t";
        std::cout << "Best fitness: " << this->best_fitness << " (Run # " << this->best_run << ")\t";
        std::cout << "Average: " << this->average_fitness << "\t";
    }
    pthread_mutex_unlock(&this->runlock);
    
    pthread_mutex_lock(&this->maplock);
    float *worst = this->GetLeastFitGenome();
    float worst_fitness = this->fitness_map[worst];
    if (worst_fitness >= fitness) {
        pthread_mutex_unlock(&this->maplock);
        if (this->output) {
            std::cout << "(Rejected)\n";
        }
    }
    if (this->output) {
        std::cout << "(Accepted)\n";
    }
    
    // Allocate space for the genome
    float *genome_buf = (float *)malloc(this->genome_size * sizeof(float));
    if (genome_buf == NULL) {
        std::cerr << "Allocation error\n";
        exit(1);
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
    if (fitness > this->best_fitness) {
        this->best_run = this->run++;
        this->best_fitness = fitness;
    }
    this->ComputeStats();
    pthread_mutex_unlock(&this->maplock);
    return 0;
}

void Evolver::ComputeStats() {
    float total = 0.0f;
    unsigned int count = 0;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += fitness;
        count++;
    }
    this->average_fitness = total / count;
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

float Evolver::GetTotalFitness() {
    float total = 0.0f;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += powf(fitness, FITNESS_PREF);
    }
    return total;
}

float * Evolver::ChooseParentFromFitnessMap(float input) {
    float total = 0.0f;
    float *ret = NULL;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += powf(fitness, FITNESS_PREF);
        ret = it->first;
        if (total > input) {
            break;
        }
    }
    return ret;
}

float * Evolver::ChooseRandomParent(float total) {
    float rnd = (float)rand()/((float)RAND_MAX/total);
    return this->ChooseParentFromFitnessMap(rnd);
}

std::pair<float *, float *> Evolver::ChooseParents() {
    float *mother = this->fitness_map.begin()->first;
    float *father = this->fitness_map.begin()->first;
    float total = this->GetTotalFitness();
    while (mother == father) {
        mother = this->ChooseRandomParent(total);
        father = this->ChooseRandomParent(total);
    }
    return std::make_pair(mother, father);
}

void Evolver::BreedGenome(float *out) {
    float *father, *mother;
    std::pair<float *, float *> parents;
    
    pthread_mutex_lock(&this->maplock);
    
    parents = this->ChooseParents();
    mother = parents.first;
    father = parents.second;
    
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
                *cur += -MUTATION_AMOUNT + (float)rand()/((float)RAND_MAX/(MUTATION_AMOUNT * 2));
            }
        }
        else {
            // Leia, I am not your father!
            *cur = *(mother + i);
            if (rnd2 < 0.05f) {
                // Mutation time!
                *cur += -MUTATION_AMOUNT + (float)rand()/((float)RAND_MAX/(MUTATION_AMOUNT * 2));
            }
        }
    }
    
    pthread_mutex_unlock(&this->maplock);
}

