#include <map>
#include <stack>
#include <vector>
#include <iostream>
#include <algorithm>
#include <unordered_set>

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
    std::cerr.precision(2);
    // 0s on the diagonal!
    for (i = 0; i < width; i++) {
        ret[i*width + i] = true;
    }
    
    for (i = 0; i < d.size(); i++) {
        unsigned int j = i + 1;
        if (! ( i % 100)) std::cerr << "Compute Distances: " << 100.0f * i / d.size() << "% done \r";
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
    
    // Switch off synchronization otherwise it's REEEAAALY slow
    fprintf(stderr, "Switching off pragma...\n");
    rc = sqlite3_exec(db, "PRAGMA synchronous = 0", NULL, NULL, &zErrMsg); 
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
         sqlite3_close(db);
         return 1;
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
    for (auto it : points) {
        if (it.second.size() < 2) continue;
        filtered[it.first] = it.second;
    }
    
    fprintf(stderr, "Inverting...\n");
    for (auto it : points) {
        cluster_items.push_back(it.second);
        cluster_item_map[cluster_item_map_offset++] = it.first;
    }
    
    fprintf(stderr, "Computing distance matrix...\n");
    distances = compute_distances(cluster_items, epsilon); 
    
    fprintf(stderr, "Clustering...\n");
    auto result = dbscan(cluster_items, distances, minpoints);
    fprintf(stderr, "Outputting...\n");
    for (auto it : result) {
        if (!it.second) continue;
        // std::cout << it.first << "\t" << cluster_item_map[it.first] <<   "\t" << it.second << "\n";
        rc = sqlite3_bind_int64(insert_statement, 1, cluster_item_map[it.first]);
        if (rc != SQLITE_OK) {
            fprintf(stderr, "ERROR: Failed to bind identifier parameter. Reason given '%s'\n", sqlite3_errmsg(db));
            return 1;
        }
        rc = sqlite3_bind_int64(insert_statement, 2, it.second);
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
    
    fprintf(stderr, "Committing...\n");
    rc = sqlite3_exec(db, "COMMIT;", NULL, NULL, &zErrMsg); 
    if (rc != SQLITE_OK) {
         fprintf(stderr, "SQL error: %s\n", zErrMsg);
         sqlite3_free(zErrMsg);
         sqlite3_close(db);
         return 1;
    }
    
    sqlite3_close(db);
}