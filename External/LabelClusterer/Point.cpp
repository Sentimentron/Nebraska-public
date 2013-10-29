//
//  Point.cpp
//  LabelCluster
//
//  Created by Richard Townsend on 28/10/2013.
//
//

#include <tuple>
#include <vector>
#include <iostream>
#include <unordered_set>
#include <stdint.h>

const unsigned int PRIMES[64] = {
    311,313,317,331,337,347,349,353,359,367,373,379,383,389,397,401,409,419,421,431,433,439,443,449,457,461,463,467,479,487,491,499,503,509,521,523,541,547,557,563,569,571,577,587,593,599,601,607,613,617,619,631,641,643,647,653,659,661,673,677,683,691,701,709
};

// MurmurHash2, 64-bit version, by Austin Appleby
uint64_t MurmurHash64A ( const void * key, int len, unsigned int seed )
{
	const uint64_t m = 0xc6a4a7935bd1e995;
	const int r = 47;
    
	uint64_t h = seed ^ (len * m);
    
	const uint64_t * data = (const uint64_t *)key;
	const uint64_t * end = data + (len/8);
    
	while(data != end)
	{
		uint64_t k = *data++;
        
		k *= m;
		k ^= k >> r;
		k *= m;
		
		h ^= k;
		h *= m;
	}
    
	const unsigned char * data2 = (const unsigned char*)data;
    
	switch(len & 7)
	{
        case 7: h ^= uint64_t(data2[6]) << 48;
        case 6: h ^= uint64_t(data2[5]) << 40;
        case 5: h ^= uint64_t(data2[4]) << 32;
        case 4: h ^= uint64_t(data2[3]) << 24;
        case 3: h ^= uint64_t(data2[2]) << 16;
        case 2: h ^= uint64_t(data2[1]) << 8;
        case 1: h ^= uint64_t(data2[0]);
	        h *= m;
	};
    
	h ^= h >> r;
	h *= m;
	h ^= h >> r;
    
	return h;
} 

uint64_t build_entry(std::unordered_set<uint64_t> point, uint64_t &count, unsigned int hash_functions) {
    uint64_t ret = 0;
    for (auto it = point.begin(); it != point.end(); ++it) {
        auto p = *it;
        for (unsigned int i = 0; i < hash_functions; i++) {
            uint64_t hash = MurmurHash64A(&p, 8, PRIMES[i]) % 64;
            ret |= (1 << hash);
        }
        count++;
    }
    return ret; 
}

void compute_bloom_filter(std::vector<uint64_t> &bloom, std::vector<uint64_t> &bloom_count, std::vector<std::unordered_set<uint64_t>> &d, unsigned int hash_functions) {
    std::cerr << "Computing bloom filter...\n";
    for (unsigned int i = 0; i < d.size(); i++) {
        if (! ( i % 100)) std::cerr << "Compute bloom filter: " << 100.0f * i / d.size() << "% done \r";
        auto point = d[i];
        bloom[i] = build_entry(point, bloom_count[i], hash_functions);
    }
    std::cerr << "\n";
}
