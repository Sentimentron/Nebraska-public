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

const char * const SELECT_QUERY = "SELECT DISTINCT document_identifier, label FROM temporary_label_%s ORDER BY label;";
const char * const INSERT_QUERY = "INSERT INTO temporary_label_%s VALUES (?, ?);";
const char * const TRUNCATE_QUERY = "DELETE FROM temporary_label_%s;";

void compute_bloom_filter(std::vector<uint64_t> &bloom, std::vector<uint64_t> &bloom_count, std::vector<std::unordered_set<uint64_t>> &d, unsigned int hash_functions);

inline float _dbscan_dist (const std::vector<uint64_t> &first,
                           const std::vector<uint64_t> &second) {
    unsigned int u, i = 0;

    u = first.size();
    if (second.size() > u) u = second.size();
    
    for (auto it = first.begin(); it != first.end(); ++it) {
        if (std::find(second.begin(), second.end(), *it) != second.end()) {
            i++;
        }
    }
     
    return 1.0 - (1.0*i)/u;
}


std::vector<bool> compute_distances(std::vector<std::vector<uint64_t>> &d, float epsilon) {
    size_t width = d.size();
    unsigned int i;
    std::vector<bool> ret (width * width); 
    // 0s on the diagonal!
    for (i = 0; i < width; i++) {
        ret[i*width + i] = true;
    }
    
    std::vector<uint64_t> bloom(d.size()), bloom_count(d.size());
        
    for (i = 0; i < d.size(); i++) {
        unsigned int j;
        if (! ( i % 100)) std::cerr << "Compute distances: " << 100.0f * i / d.size() << "% done \r";
        for (j = i + 1; j < d.size(); j++) {
            off_t o;
            float distance;
            
            o = (i * width) + j;
            distance = _dbscan_dist(d[i], d[j]);
            //fprintf(stderr, "d:%f\n", distance);
            
            ret[o] = distance < epsilon;
            o = (j * width) + i;
            ret[o] = distance < epsilon;
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

std::map<const uint64_t, uint64_t> dbscan(const std::vector<std::vector<uint64_t>> &d,
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
                neighbours.pop();
                if (visited_neighbours.find(neighbour) != visited_neighbours.end()) continue;
                visited_neighbours.insert(neighbour);
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

static int query_callback_domains(void *domains_raw, int argc, char **argv, char **col) {
    auto *domains = (std::vector<uint64_t> *)domains_raw;
    uint64_t domain = strtoul(argv[0], NULL, 10);
    domains->push_back(domain);
    return 0;
}

std::vector<uint64_t> get_domains(sqlite3 *db) {
    char *zErrMsg = NULL;
    std::vector<uint64_t> domains;
    int rc = sqlite3_exec(db, "SELECT DISTINCT label FROM label_domains ORDER BY label ASC", query_callback_domains, &domains, &zErrMsg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_close(db);
        exit(1);
    }
    return domains;
}

std::vector<std::vector<uint64_t>> get_domain_combos(std::map<uint64_t, std::vector<uint64_t>> doc_map) {
    // Generates the combinations of labels which are possible
    // Shameless copy from http://stackoverflow.com/questions/9430568/generating-combinations-in-c
    
    std::vector<std::vector<uint64_t>> ret;
    for (auto &kv : doc_map) {
        bool matching = false;
        for (auto candidate : ret) {
            matching |= candidate == kv.second;
            if (matching) break;
        }
        if (matching) continue;
        ret.push_back(kv.second);
    }
    
    return ret;
}

static int callback_doc_domains(void *map, int argc, char **argv, char **col) {
    auto *points = (std::map<uint64_t, std::vector<uint64_t>> *)map;
    uint64_t identifier, label;
    
    identifier = strtoul(argv[0], NULL, 10);
    label      = strtoul(argv[1], NULL, 10);
    
    auto it = points->find(identifier);
    if (it == points->end()) {
        auto set = std::vector<uint64_t>();
        set.push_back(label);
        points->insert(std::pair<uint64_t,std::vector<uint64_t>>(identifier, set));
    }
    else {
        it->second.push_back(label);
    }
    
    return 0;
}

std::map<uint64_t, std::vector<uint64_t>> generate_doc_domain_map(sqlite3 *db) {
    int rc;
    char *zErrMsg = NULL;
    std::map<uint64_t, std::vector<uint64_t>> ret;
    
    rc = sqlite3_exec(db, "SELECT DISTINCT document_identifier, label FROM label_domains", callback_doc_domains, &ret, &zErrMsg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL Error: %s\n", zErrMsg);
        sqlite3_close(db);
        exit(1);
    }
    
    return ret;
}

std::map<uint64_t, std::vector<uint64_t>> generate_doc_label_map(sqlite3 *db, char *src_table) {
    size_t query_len;
    char *query;
    int rc;
    char *zErrMsg = NULL;
    std::map<uint64_t, std::vector<uint64_t>> ret;
    // Create the query string
    query_len = strlen(SELECT_QUERY);
    query = (char *)calloc(query_len + 1, 1);
    if (query == NULL) {
        fprintf(stderr, "Allocation error\n");
        exit(2);
    }
    memcpy(query, SELECT_QUERY, query_len);
    query_len = snprintf(query, 0, SELECT_QUERY, src_table) + 1;
    query = (char *)realloc(query, query_len);
    snprintf(query, query_len, SELECT_QUERY, src_table);
    
    fprintf(stderr, "Executing '%s'...\n", query);
    rc = sqlite3_exec(db, query, callback_doc_domains, &ret, &zErrMsg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n", zErrMsg);
        sqlite3_free(zErrMsg);
        sqlite3_close(db);
        exit(1);
    }
    free(query);
    return ret;
}

std::map<uint64_t, uint64_t> cluster(sqlite3 *db, char *src_table, float epsilon, int minpoints) {
    std::vector<uint64_t> domains = get_domains(db);
    std::map<uint64_t, std::vector<uint64_t>> doc_map = generate_doc_domain_map(db);
    std::map<uint64_t, std::vector<uint64_t>> label_map = generate_doc_label_map(db, src_table);
    std::vector<std::vector<uint64_t>> combos = get_domain_combos(doc_map);

    std::map<uint64_t, uint64_t> ret;
    unsigned int cluster_counter = 0;
    for (auto combo : combos) {
        std::vector<uint64_t> identifiers; 
        std::map<uint64_t, std::vector<uint64_t>> points, filtered;
        std::vector<bool> distances;
        int cluster_item_map_offset = 0;
        std::map<uint64_t, uint64_t> cluster_item_map;
        std::vector<std::vector<uint64_t>> cluster_items;
        fprintf(stderr, "Filtering...\n");
        for (auto &kv : doc_map) {
            if (kv.second == combo) {
                identifiers.push_back(kv.first);
            }
        }
        for (auto &kv : label_map) {
            auto id = kv.first;
            auto it = std::find(identifiers.begin(), identifiers.end(), id);
            if (it == identifiers.end()) continue;
            points.insert(kv);
        }
        
        // Points now contains everything with this combination of domains
        // Now get rid of everything with only one label
        for (auto it = points.begin(); it != points.end(); ++it) {
            if (it->second.size() < 2) continue;
            filtered[it->first] = it->second;
        }
        
        for (auto it = filtered.begin(); it != filtered.end(); ++it) {
            cluster_items.push_back(it->second);
            cluster_item_map[cluster_item_map_offset++] = it->first;
        }
        // Now compute distances
        distances = compute_distances(cluster_items, epsilon);
        // Now cluster
        fprintf(stderr, "Clustering...\n");
        std::map<const uint64_t, uint64_t> result = dbscan(cluster_items, distances, minpoints);
        // Transcribe the result
        std::map<uint64_t, uint64_t> cluster_map;
        for (auto& kv : result) {
            int mapped_cluster_id = 0;
            // Cluster outputs doc_id -> cluster
            if (kv.second) {
                // See if this cluster has already been seen
                auto it = cluster_map.find(kv.second);
                if (it == cluster_map.end()) {
                    // If it hasn't, make a note of it
                    cluster_counter++;
                    cluster_map.insert(std::pair<uint64_t, uint64_t>(kv.second, cluster_counter));
                    mapped_cluster_id = cluster_counter;
                }
                else {
                    mapped_cluster_id = cluster_map[it->first];
                }
            }
            ret.insert(std::pair<uint64_t, uint64_t>(cluster_item_map[kv.first], mapped_cluster_id));
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
    
    fprintf(stderr, "Clustering...\n");
    auto result = cluster(db, src_table, epsilon, minpoints);
    fprintf(stderr, "Outputting...\n");
    for (auto it = result.begin(); it != result.end(); ++it) {
        // std::cout << it.first << "\t" << cluster_item_map[it.first] <<   "\t" << it.second << "\n";
        rc = sqlite3_bind_int64(insert_statement, 1, it->first);
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
    
    sqlite3_close(db);
}
