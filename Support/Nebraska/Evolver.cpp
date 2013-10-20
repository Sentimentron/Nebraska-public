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

Evolver::~Evolver() {
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto first = it->first;
        free(first);
    }
}

int Evolver::PushGenomeFitness(const float *genome, float fitness) {
    
    pthread_mutex_lock(&this->runlock);
    this->run++;
    if (this->output) {
        std::cout.precision(4);
        std::cout << std::fixed;
        std::cout << "#(" << this->run << ") Current fitness: " << fitness << "\t";
        std::cout << "Best fitness: " << this->best_fitness << " (Run # " << this->best_run << ")\t";
        std::cout << "Average: " << this->average_fitness << "\t";
    }
    
    pthread_mutex_lock(&this->maplock);
    float *worst = this->GetLeastFitGenome();
    if (worst == NULL) {
        std::cerr << "Failed to find the worst genome!\n";
        exit(1);
    }
    float worst_fitness = this->fitness_map[worst];
    if (worst_fitness >= fitness) {
        pthread_mutex_unlock(&this->maplock);
        if (this->output) {
            std::cout << "(Rejected)\n";
        }
        pthread_mutex_unlock(&this->runlock);
        return 0;
    }
    if (this->output) {
        std::cout << "(Accepted)\n";
    }
    pthread_mutex_unlock(&this->runlock);
    int ret = this->_PushGenomeFitness(genome, fitness);
    pthread_mutex_unlock(&this->maplock);
    return ret;
}

int Evolver::_PushGenomeFitness(const float *genome, float fitness) {
    
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
    if (!(this->run % 500)) {
        this->count++;
        this->mutation_amount *= 0.95f;
        this->mutation_rate *= 0.85f;
    }
    // Remove the least fit genomes
    for (int i = this->cur; i > this->count; i--) {
        float *cur = this->GetLeastFitGenome();
        if (cur == NULL) {
            std::cerr << "Failed to find the worst genome!\n";
            exit(1);
        }
        RemoveGenome(cur);
    }
    // Insert the genome into the fitness map
    this->fitness_map[genome_buf] = fitness;
    if (fitness > this->best_fitness) {
        this->best_run = this->run++;
        this->best_fitness = fitness;
    }
    this->ComputeStats();
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
        exit(1);
    }
    free(genome);
    if (this->cur) this->cur--;
}

float *Evolver::GetMostFitGenome() {
    float best_fitness = 0.0f;
    float *best_genome = NULL;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto genome = it->first;
        auto fitness = it->second;
        if (fitness > best_fitness) {
            best_genome = genome;
            best_fitness = fitness;
        }
    }
    return best_genome;
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
        *cur = this->Random(-0.1f, 0.1f);
    }
}

float Evolver::GetTotalFitness() {
    float total = 0.0f;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += powf(fitness, this->fitness_pref);
    }
    return total;
}

float * Evolver::ChooseParentFromFitnessMap(float input) {
    float total = 0.0f;
    float *ret = NULL;
    for (auto it = this->fitness_map.begin(); it != this->fitness_map.end(); it++) {
        auto fitness = it->second;
        total += powf(fitness, this->fitness_pref);
        ret = it->first;
        if (total > input) {
            break;
        }
    }
    return ret;
}

float * Evolver::ChooseRandomParent(float total) {
    float rnd = this->Random(0.0f, total);
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
    for (int i = 0; i < this->dont_mutate_beyond; i++) {
        float *cur = out + i;
        float rnd = this->Random(0.0f, 1.0f);
        float rnd2 = this->Random(0.0f, 1.0f);
        if (rnd <= 0.5f) {
            // Luke, I am your father!
            *cur = *(father + i);
            if (rnd2 < this->mutation_rate) {
                // Mutation time!
                *cur += this->Random(-this->mutation_amount, +this->mutation_amount);
            }
        }
        else {
            // Leia, I am not your father!
            *cur = *(mother + i);
            if (rnd2 <  this->mutation_rate) {
                // Mutation time!
                *cur += this->Random(-this->mutation_amount, +this->mutation_amount);
            }
        }
    }
    
    pthread_mutex_unlock(&this->maplock);
}

