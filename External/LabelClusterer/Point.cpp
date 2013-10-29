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

uint64_t build_entry(std::unordered_set<uint64_t> point, uint64_t &count) {
    uint64_t ret = 0;
    for (auto it = point.begin(); it != point.end(); ++it) {
        auto p = *it;
        uint64_t hash1 = MurmurHash64A(&p, 8, 97 ) % 64;
        uint64_t hash2 = MurmurHash64A(&p, 8, 108) % 64;
        ret |= (1 << hash1) | (1 << hash2);
        count++;
    }
    return ret; 
}

void compute_bloom_filter(std::vector<uint64_t> &bloom, std::vector<uint64_t> &bloom_count, std::vector<std::unordered_set<uint64_t>> &d) {
    std::cerr << "Computing bloom filter...\n";
    for (unsigned int i = 0; i < d.size(); i++) {
        if (! ( i % 100)) std::cerr << "Compute bloom filter: " << 100.0f * i / d.size() << "% done \r";
        auto point = d[i];
        bloom[i] = build_entry(point, bloom_count[i]);
    }
    std::cerr << "\n";
}