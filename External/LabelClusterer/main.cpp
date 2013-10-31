#include <map>
#include <stack>
#include <vector>
#include <iostream>
#include <algorithm>
#include <unordered_set>
#include <math.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

#include "version.h"

const char * const SELECT_QUERY = "SELECT document_identifier, label FROM temporary_label_%s;"; 
const char * const INSERT_QUERY = "INSERT INTO temporary_label_%s VALUES (?, ?);";
const char * const TRUNCATE_QUERY = "DELETE FROM temporary_label_%s;";

void compute_bloom_filter(std::vector<uint64_t> &bloom, std::vector<uint64_t> &bloom_count, std::vector<std::unordered_set<uint64_t>> &d, unsigned int hash_functions);

inline float _dbscan_dist (const std::unordered_set<uint64_t> &first,
                           const std::unordered_set<uint64_t> &second) {
    unsigned int u, i = 0;

    u = first.size();
    if (second.size() > u) u = second.size();
    
    for (auto it = first.begin(); it != first.end(); ++it) {
        if (second.find(*it) != second.end()) {
            i++;
        }
    }
     
    return 1.0 - (1.0*i)/u;
}

inline int popcount(uint64_t x) {
    int count;
    for (count=0; x; count++)
        x &= x-1;
    return count;
}

const float BM_ELEMENT_ESTIMATE[64] = {0., 0.503947, 1.01596, 1.5363, 2.06523, 2.60306, 3.15008, 3.70662, 
4.273, 4.8496, 5.43677, 6.03492, 6.64446, 7.26584, 7.89952, 8.54601, 
9.20583, 9.87954, 10.5677, 11.2711, 11.9902, 12.7259, 13.4788, 14.25, 
15.0401, 15.8503, 16.6815, 17.5349, 18.4117, 19.3131, 20.2407, 
21.196, 22.1807, 23.1967, 24.2459, 25.3308, 26.4537, 27.6175, 
28.8252, 30.0802, 31.3865, 32.7484, 34.1709, 35.6595, 37.2208, 
38.8622, 40.5924, 42.4214, 44.3614, 46.4267, 48.6344, 51.0059, 
53.5672, 56.3516, 59.4015, 62.7731, 66.5421, 70.8151, 75.748, 
81.5822, 88.7228, 97.9287, 110.904, 133.084};

inline float estimate_bm_element_count(uint64_t b, unsigned int hash_functions) {
    int c = __builtin_popcount(b);
    // fprintf(stderr, "%d\n", c);
    return -64.0 / hash_functions * logf(1.0f - (c/64.0f));
}

std::vector<bool> compute_distances(std::vector<std::unordered_set<uint64_t>> &d, float epsilon, unsigned int hash_functions) {
    size_t width = d.size();
    unsigned int i;
    std::vector<bool> ret (width * width); 
    // 0s on the diagonal!
    for (i = 0; i < width; i++) {
        ret[i*width + i] = true;
    }
    
    std::vector<uint64_t> bloom(d.size()), bloom_count(d.size());
    compute_bloom_filter(bloom, bloom_count, d, hash_functions);
    
    const float epsilon_comp_const = (2.0f - epsilon);
    
    for (i = 0; i < d.size(); i++) {
        unsigned int j = i + 1;
        if (! ( i % 100)) std::cerr << "Compute distances: " << 100.0f * i / d.size() << "% done \r";
        for (j = i + 1; j < d.size(); j++) {
            if (!(bloom[i] & bloom[j])) continue;
            uint64_t a = bloom_count[i];
            uint64_t b = bloom_count[j];
            float c = estimate_bm_element_count(bloom[i] | bloom[j], hash_functions); 
            
            //fprintf(stderr, "a: %d\tb: %d\tc: %f\te: %f\t", a, b, c, epsilon_comp_const);
            
            // if (a + b > epsilon_comp_const * c) continue;
            
            // if ((logf(-(a-64)*(b-64)*(c-64)/262144.0f)/logf(1.0f-c/64.0f)) > epsilon - 1.0f) continue;
            // if ((a - 64) *(b - 64) * (c - 64) > powf(1-c/64.0f, epsilon-1.0f) * -262144) continue;

            off_t o;
            float distance;
            
            o = (i * width) + j;
            distance = _dbscan_dist(d[i], d[j]);
            //fprintf(stderr, "d:%f\n", distance);
            
            ret[o] = distance < epsilon;
            o = (j * width) + i;
            ret[i] = distance < epsilon;
        }
    }

    std::cerr << "\n";
    return ret;
}

void dbscan_region_query (std::stack<uint64_t> &neighbours,
    const off_t point_offset,
    const std::vector<bool> &distances,
    const off_t max_offset) {
    
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
        // For each unvisited point...
        // Mark this point as visited
        visited.insert(point_offset);
        // Get neighbours to this point 
        std::stack<uint64_t> neighbours;
        std::unordered_set<uint64_t> visited_neighbours;
        dbscan_region_query(neighbours, point_offset, distances, d.size());
        // If less than the minum number of points...
        if (neighbours.size() < min_points) {
            ret[point_offset] = 0; // Noise
        }
        // Otherwise expand the cluster...
        else {
            // Allocate a new cluster and assign it
            cluster_counter++;
            ret[point_offset] = cluster_counter;
            clustered.insert(point_offset);
            // Visit each neighbour point...
            while(!neighbours.empty()) {
                auto neighbour = neighbours.top();
                // if (visited_neighbours.find(neighbour) != visited_neighbours.end()) continue;
                visited_neighbours.insert(neighbour);
                neighbours.pop();
                // If neighbour hasn't been visited...
                if (visited.find(neighbour) == visited.end()) {
                    visited.insert(neighbour); // Mark the point as visited
                    // Retrieve secondary neighbours...
                    std::stack<uint64_t> secondary_neighbours;
                    dbscan_region_query(secondary_neighbours, neighbour, distances, d.size());
                    if (secondary_neighbours.size() >= min_points) {
                        while(!secondary_neighbours.empty()) {
                            auto n = secondary_neighbours.top();
                            secondary_neighbours.pop();
                            if (visited_neighbours.find(n) != visited_neighbours.end()) continue;
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

void _as_ltargv(int i, int argc) {
    if (i < argc) return; 
    fprintf(stderr, "Expected a parameter!\n");
    exit(1);
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
    
    int truncate = 0;
    
    sqlite3_stmt *insert_statement = NULL;
    float epsilon = 0.5f;
    unsigned int minpoints = 2; 
    unsigned int hash_functions = 0;
    
    // Stored as identifier -> [labels]
    std::map<const uint64_t, std::unordered_set<uint64_t>> points;
    
    // Parse command line arguments 
    for (int i = 0; i < argc; i++) {
        if (!strcmp(argv[i],"--db")) {
            _as_ltargv(i+1, argc);
            db_location = argv[i+1];
        }
        else if (!strcmp(argv[i],"--src")) {
            _as_ltargv(i+1, argc);
            src_table = argv[i+1];
        }
        else if (!strcmp(argv[i], "--dest")) {
            _as_ltargv(i+1, argc);
            dest_table = argv[i+1];
        }
        else if (!strcmp(argv[i], "--truncate")) {
            truncate = 1;
        }
        else if (!strcmp(argv[i], "--minpoints")) {
            _as_ltargv(i+1, argc);
            if(!sscanf(argv[i+1], "%u", &minpoints)) {
                fprintf(stderr, "--minpoints [unsigned int]\n");
                return 1;
            }
        }
        else if (!strcmp(argv[i], "--epsilon")) {
            _as_ltargv(i+1, argc);
            if(!sscanf(argv[i+1], "%f", &epsilon)) {
                fprintf(stderr, "--epsilon [float]\n");
                return 1;
            }
        }
        else if (!strcmp(argv[i], "--version")) {
            printf("%s\n", VERSION);
            exit(0);
        }
	else if (!strcmp(argv[i], "--hashfunctions")) {
            _as_ltargv(i+1, argc);
            if(!sscanf(argv[i+1], "%u", &hash_functions)) {
                fprintf(stderr, "--hashfunctions [unsigned int]\n");
                return 1;
            }
	}
    }

    if (!hash_functions) {
        fprintf(stderr, "Error: --hashfunctions must be specified.\n");
        return 1;
    }

    if (hash_functions > 64) { 
        fprintf(stderr, "Error: number of hash functions doesn't make sense!\n");
        return 1;
    }
    
    // Open the database 
    rc = sqlite3_open(db_location, &db);
    if (rc) {
        fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return 1;
    }
    
    if (truncate) {
        // If truncating the table, need to create the query 
        query_len = strlen(TRUNCATE_QUERY);
        query = (char *)calloc(query_len + 1, 1);
        if (query == NULL) {
            fprintf(stderr, "Allocation error\n");
            return 2;
        }
        memcpy(query, TRUNCATE_QUERY, query_len);
        query_len = snprintf(query, 0, TRUNCATE_QUERY, dest_table) + 1;
        query = (char *)realloc(query, query_len);
        snprintf(query, query_len, TRUNCATE_QUERY, dest_table);
        fprintf(stderr, "Executing '%s'...\n", query);
        rc = sqlite3_exec(db, query, query_callback, &points, &zErrMsg);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "SQL error: %s\n", zErrMsg);
            sqlite3_free(zErrMsg);
            sqlite3_close(db);
            return 1;
        }
        free(query);
    }
    
    // Switch off synchronization otherwise it's REEEAAALY slow
    /*fprintf(stderr, "Switching off pragma...\n");
    rc = sqlite3_exec(db, "PRAGMA synchronous = 0", NULL, NULL, &zErrMsg);
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
         sqlite3_close(db);
         return 1;
    }*/
    
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
    
    fprintf(stderr, "Executing '%s'...\n", query);
    rc = sqlite3_exec(db, query, query_callback, &points, &zErrMsg);
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
         sqlite3_close(db);
         return 1;
    }
    free(query);
        
    std::vector<bool> distances;
    std::vector<std::unordered_set<uint64_t>> cluster_items; 
    // Stores the relationship between offset in cluster_items
    // and document_id (document_id -> cluster_items_offset)
    std::map<uint64_t, uint64_t> cluster_item_map;
    unsigned int cluster_item_map_offset = 0;
    
    fprintf(stderr, "Preparing insert query...\n");
    // Create the insert string
    query_len = strlen(INSERT_QUERY);
    query = (char *)calloc(query_len + 1, 1);
    if (query == NULL) {
        fprintf(stderr, "Allocation error\n");
        return 2;
    }
    memcpy(query, INSERT_QUERY, query_len);
    query_len = snprintf(query, 0, INSERT_QUERY, dest_table) + 1;
    query = (char *)realloc(query, query_len);
    snprintf(query, query_len, INSERT_QUERY, dest_table);
    fprintf(stderr, "\tInsert query is '%s'...\n", query);
    rc = sqlite3_prepare(db, query, -1, &insert_statement, 0);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "ERROR: Failed to prepare statement. Reason given '%s'\n", sqlite3_errmsg(db));
        return 1;
    }
    
    fprintf(stderr, "Filtering...\n");
    std::map<const uint64_t, std::unordered_set<uint64_t>> filtered;
    for (auto it = points.begin(); it != points.end(); ++it) {
        if (it->second.size() < 2) continue;
        filtered[it->first] = it->second;
    }
    
    fprintf(stderr, "Inverting...\n");
    for (auto it = points.begin(); it != points.end(); ++it) {
        cluster_items.push_back(it->second);
        cluster_item_map[cluster_item_map_offset++] = it->first;
    }
    
    fprintf(stderr, "Computing distance matrix...\n");
    distances = compute_distances(cluster_items, epsilon, hash_functions); 
    
    fprintf(stderr, "Clustering...\n");
    auto result = dbscan(cluster_items, distances, minpoints);
    fprintf(stderr, "Outputting...\n");
    for (auto it = result.begin(); it != result.end(); ++it) {
        if (!it->second) continue;
        // std::cout << it.first << "\t" << cluster_item_map[it.first] <<   "\t" << it.second << "\n";
        rc = sqlite3_bind_int64(insert_statement, 1, cluster_item_map[it->first]);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "ERROR: Failed to bind identifier parameter. Reason given '%s'\n", sqlite3_errmsg(db));
            return 1;
        }
        rc = sqlite3_bind_int64(insert_statement, 2, it->second);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "ERROR: Failed to bind cluster parameter. Reason given '%s'\n", sqlite3_errmsg(db));
            return 1;
        }
        sqlite3_step(insert_statement);
        rc = sqlite3_reset(insert_statement);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "ERROR: Failed to reset insert statement. Reason given '%s'\n", sqlite3_errmsg(db));
            return 1;
        }
    }
    
    /*fprintf(stderr, "Committing...\n");
    rc = sqlite3_exec(db, "COMMIT;", NULL, NULL, &zErrMsg); 
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
         sqlite3_close(db);
         return 1;
    }*/
    
    sqlite3_close(db);
}
