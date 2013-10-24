#include <map>
#include <stack>
#include <vector>
#include <iostream>
#include <unordered_set>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

const char * const SELECT_QUERY = "SELECT document_identifier, label FROM temporary_label_%s;"; 

inline float _dbscan_dist (const std::unordered_set<uint64_t> &first,
                   const std::unordered_set<uint64_t> &second) {
    unsigned int u = 0, i = 0;
    
    for (auto t : first) {
        u++;
        if (second.find(t) != second.end()) {
            i++;
        }
    }
    
    for (auto t : second) {
        if (first.find(t) == first.end()) {
            u++;
        }
    }
    
    return 1.0 - 1.0*i/u;
}

std::vector<bool> compute_distances(std::vector<std::unordered_set<uint64_t>> &d, float epsilon) {
    size_t width = d.size();
    unsigned int i;
    std::vector<bool> ret (width * width); 

    // 0s on the diagonal!
    for (i = 0; i < width; i++) {
        ret[i*width + i] = true;
    }
    
    for (i = 0; i < d.size(); i++) {
        unsigned int j = i + 1;
        for (j = i + 1; j < d.size(); j++) {
            off_t o;
            float distance; 
            
            o = (i * width) + j;
            distance = _dbscan_dist(d[i], d[j]);
            
            ret[o] = distance < epsilon;
            o = (j * width) + i;
            ret[i] = distance < epsilon; 
        }
    }
    
    return ret;
}

void dbscan_region_query (std::stack<uint64_t> &neighbours,
    const uint64_t point_offset,
    const std::vector<bool> &distances,
    size_t max_offset) {
    
    off_t offset = point_offset; 
    for (off_t i = offset; i < max_offset; i++) {
        if (distances[offset * max_offset + i]) {
            neighbours.push(i);
        }
    }
    
}

std::map<const uint64_t, uint64_t> dbscan(const std::vector<std::unordered_set<uint64_t>> &d,
                                    const std::vector<bool> distances, 
                                    const unsigned int min_points) {
    std::map<const uint64_t, uint64_t> ret;
    std::unordered_set<uint64_t> visited, clustered; 
    uint64_t cluster_counter = 0;
    for (uint64_t point_offset = 0; point_offset < d.size(); point_offset++) {
        auto point = d[point_offset];
        if (visited.find(point_offset) != visited.end()) continue;
        visited.insert(point_offset);
        // 
        std::stack<uint64_t> neighbours;
        dbscan_region_query(neighbours, point_offset, distances, d.size());
        if (neighbours.size() < min_points) {
            ret[point_offset] = 0; // Noise
        }
        else {
            cluster_counter++;
            ret[point_offset] = cluster_counter;
            clustered.insert(point_offset);
            while(!neighbours.empty()) {
                auto neighbour = neighbours.top();
                neighbours.pop();
                if (visited.find(neighbour) == visited.end()) {
                    visited.insert(neighbour);
                    std::stack<uint64_t> secondary_neighbours;
                    const std::unordered_set<uint64_t> &src_point = d[neighbour];
                    dbscan_region_query(secondary_neighbours, neighbour, distances, d.size());
                    if (secondary_neighbours.size() >= min_points) {
                        while(!secondary_neighbours.empty()) {
                            auto n = secondary_neighbours.top();
                            secondary_neighbours.pop();
                            neighbours.push(n);
                        }
                    }
                }
                if (clustered.find(neighbour) == clustered.end()) {
                    ret[neighbour] = cluster_counter;
                    clustered.insert(neighbour);
                }
            }
        }
    }
    return ret;
}                                                 

static int query_callback(void *map, int argc, char **argv, char **col) {
    auto *points = (std::map<uint64_t, std::unordered_set<uint64_t>> *)map;
    uint64_t identifier, label;
    
    identifier = strtoul(argv[0], NULL, 10);
    label      = strtoul(argv[1], NULL, 10);
    
    auto it = points->find(identifier);
    if (it == points->end()) {
        auto set = std::unordered_set<uint64_t>();
        set.insert(label);
        points->insert(std::pair<uint64_t,std::unordered_set<uint64_t>>(identifier, set));
    }
    else {
        it->second.insert(label);
    }
        
    return 0;
}

int main(int argc, char **argv) {

    char *db_location = NULL;
    char *src_table   = NULL; 
    char *dest_table  = NULL;
    char *query;
    size_t query_len;
   
    sqlite3 *db       = NULL;
    char *zErrMsg     = NULL;
    int rc = 0; 
    
    // Stored as identifier -> [labels]
    std::map<const uint64_t, std::unordered_set<uint64_t>> points;
    
    // Parse command line arguments 
    for (int i = 0; i < argc-1; i++) {
        if (!strcmp(argv[i],"--db")) {
            db_location = argv[i+1];
        }
        else if (!strcmp(argv[i],"--src")) {
            src_table = argv[i+1];
        }
        else if (!strcmp(argv[i], "--dest")) {
            dest_table = argv[i+1];
        }
    }
    
    // Create the query string
    query_len = strlen(SELECT_QUERY);
    query = (char *)calloc(query_len + 1, 1);
    if (query == NULL) {
        fprintf(stderr, "Allocation error\n");
        return 2;
    }
    memcpy(query, SELECT_QUERY, query_len);
    query_len = snprintf(query, 0, SELECT_QUERY, src_table) + 1;
    query = (char *)realloc(query, query_len);
    snprintf(query, query_len, SELECT_QUERY, src_table);

    // Open the database 
    rc = sqlite3_open(db_location, &db);
    if (rc) {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return 1;
    }
    
    fprintf(stderr, "Executing '%s'...\n", query);
    rc = sqlite3_exec(db, query, query_callback, &points, &zErrMsg);
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
    }
    else {
        
        std::vector<bool> distances;
        std::vector<std::unordered_set<uint64_t>> cluster_items; 
        // Stores the relationship between offset in cluster_items
        // and document_id (document_id -> cluster_items_offset)
        std::map<uint64_t, uint64_t> cluster_item_map;
        unsigned int cluster_item_map_offset = 0;
        
        fprintf(stderr, "Filtering...\n");
        std::map<const uint64_t, std::unordered_set<uint64_t>> filtered;
        for (auto it : points) {
            if (it.second.size() < 2) continue;
            filtered[it.first] = it.second;
        }
        
        fprintf(stderr, "Inverting...\n");
        for (auto it : filtered) {
            cluster_items.push_back(it.second);
            cluster_item_map[cluster_item_map_offset++] = it.first;
        }
        
        fprintf(stderr, "Computing distance matrix...\n");
        distances = compute_distances(cluster_items, 0.3); 
        
        fprintf(stderr, "Clustering...\n");
        auto result = dbscan(cluster_items, distances, 3);
        for (auto it : result) {
            if (!it.second) continue;
            std::cout << it.first << "\t" << cluster_item_map[it.first] <<   "\t" << it.second << "\n";
        }
    }
    
    sqlite3_close(db);
}