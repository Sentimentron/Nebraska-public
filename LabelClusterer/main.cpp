#include <map>
#include <stack>
#include <iostream>
#include <unordered_set>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

const char * const SELECT_QUERY = "SELECT document_identifier, label FROM temporary_label_%s;"; 

inline float _dbscan_dist (const std::unordered_set<uint64_t> first,
                   const std::unordered_set<uint64_t> second) {
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

std::stack<std::pair<const uint64_t, std::unordered_set<uint64_t>>> dbscan_region_query(
    std::pair<const uint64_t, std::unordered_set<uint64_t>> point, 
    const std::map<const uint64_t, std::unordered_set<uint64_t>> &d,
    float epsilon) {
    std::stack<std::pair<const uint64_t, std::unordered_set<uint64_t>>> ret; 
    for (auto _point : d) {
        if(_dbscan_dist(point.second, _point.second) < epsilon) {
            ret.push(_point);
        }
    }
    return ret;
}

std::map<const uint64_t, uint64_t> dbscan(const std::map<const uint64_t, std::unordered_set<uint64_t>> &d,
                                    const float epsilon, const unsigned int min_points) {
    std::map<const uint64_t, uint64_t> ret;
    std::unordered_set<uint64_t> visited, clustered; 
    uint64_t cluster_counter = 0;
    for(auto point : d) {
        std::cout << "DBSCAN " << visited.size() << "\t" << d.size() << "\n";
        if (visited.find(point.first) != visited.end()) continue;
        visited.insert(point.first);
        // 
        auto neighbours = dbscan_region_query(point, d, epsilon);
        if (neighbours.size() < min_points) {
            ret[point.first] = 0; // Noise
        }
        else {
            cluster_counter++;
            ret[point.first] = cluster_counter;
            clustered.insert(point.first);
            while(!neighbours.empty()) {
                auto neighbour = neighbours.top();
                neighbours.pop();
                if (visited.find(neighbour.first) == visited.end()) {
                    visited.insert(neighbour.first);
                    auto secondary_neighbours = dbscan_region_query(neighbour, d, epsilon);
                    if (secondary_neighbours.size() >= min_points) {
                        while(!secondary_neighbours.empty()) {
                            auto n = secondary_neighbours.top();
                            secondary_neighbours.pop();
                            neighbours.push(n);
                        }
                    }
                }
                if (clustered.find(neighbour.first) == clustered.end()) {
                    ret[neighbour.first] = cluster_counter;
                    clustered.insert(neighbour.first);
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
        auto result = dbscan(points, 0.3, 2);
    }
    
    
    for (auto it = points.begin(); it != points.end(); ++it) {
        std::cout << it->first << "\t";
        for (auto it2 = it->second.begin(); it2 != it->second.end(); ++it2) {
            std::cout << *it2 << " ";
        }
        std::cout << "\n";
    }
    
    sqlite3_close(db);
}