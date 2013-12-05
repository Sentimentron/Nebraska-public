#include <map>
#include <stack>
#include <vector>
#include <iostream>
#include <algorithm>
#include <unordered_set>
#include <list>
#include <math.h>

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>

#include "version.h"

const char * const SELECT_QUERY = "SELECT document_identifier, label FROM temporary_label_%s";
const char * const INSERT_QUERY = "INSERT INTO temporary_label_%s VALUES (?, ?);";
const char * const TRUNCATE_QUERY = "DELETE FROM temporary_label_%s;";

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

double distance(const uint64_t src_identifier, const uint64_t dest_identifier,
    const std::map<uint64_t, std::vector<uint64_t>> &doc_map
    ) {
    const std::vector<uint64_t> first = doc_map.at(src_identifier);
    const std::vector<uint64_t> second = doc_map.at(dest_identifier);
    return _dbscan_dist(first, second);
}

void dbscan_region_query (std::list<uint64_t> &neighbours,
    const uint64_t src_identifier,
    const std::map<uint64_t, std::vector<uint64_t>> &doc_map,
    const std::map<uint64_t, std::vector<uint64_t>> &label_map,
    const float epsilon
    ) {

    std::unordered_set<uint64_t> candidates;
    std::vector<uint64_t> labels = doc_map.at(src_identifier);
    for (auto label : labels) {
        std::vector<uint64_t> doc_identifiers = label_map.at(label);
        for (auto identifier : doc_identifiers) {
            candidates.insert(identifier);
        }
    }

    for (auto candidate : candidates) {
        if (distance(src_identifier, candidate, doc_map) < epsilon) {
            neighbours.push_back(candidate);
        }
    }

}

std::map<const uint64_t, uint64_t> dbscan(std::list<uint64_t> identifiers,
                                          // identifiers is a list of document identifiers we're clustering
                                          const std::map<uint64_t, std::vector<uint64_t>> doc_map,
                                          // this is a list of document_identifiers -> cluster source labels
                                          const std::map<uint64_t, std::vector<uint64_t>> label_map,
                                          // This is the inverse of the above
                                          const float epsilon,
                                          const unsigned int min_points) {
    std::map<const uint64_t, uint64_t> ret;
    std::unordered_set<uint64_t> visited, clustered;
    uint64_t cluster_counter = 0;
    while (visited.size() < doc_map.size()) {
        //fprintf(stderr, "MAIN LOOP %d\t%d\n", visited.size(), doc_map.size());
        fprintf(stderr, "Clustering... %f\r", visited.size() * 100.0 / doc_map.size());
        uint64_t cluster_identifier;
        std::list<uint64_t> neighbours;
        // Get the next identifier
        uint64_t cur = identifiers.back();
        identifiers.pop_back();
        visited.insert(cur);
        // Should be there for one anooooother!
        dbscan_region_query(neighbours, cur, doc_map, label_map, epsilon);
        //fprintf(stderr, "neighbours %d\t%d\n", neighbours.size(), min_points);
        if (neighbours.size() < min_points) {
            // Mark as noise
            while(neighbours.size() > 0) {
                auto neigbour = neighbours.back();
                neighbours.pop_back();
                ret[neigbour] = 0;
            }
            continue;
        }
        // Not noise - allocate new cluster and add cur to it
        cluster_counter++;
        ret[cur] = cluster_counter;
        // Go through the neighbours and do a range query for them
        while (neighbours.size() > 0) {
            //fprintf(stderr, "neighbours loop %d\n", neighbours.size());
            uint64_t cur = neighbours.back();
            neighbours.pop_back();
            // Search for cur in visited
            if (visited.find(cur) == visited.end()) {
                std::list<uint64_t> neighbours2;
                // Not yet visited
                visited.insert(cur);
                // Look at the neighbouring region
                dbscan_region_query(neighbours2, cur, doc_map, label_map, epsilon);
                //fprintf(stderr, "neighbours2 loop %d\t%d\n", neighbours2.size(), min_points);
                if (neighbours2.size() >= min_points) {
                    for (auto neighbour : neighbours2) {
                        if (std::find(neighbours.begin(), neighbours.end(), neighbour) == neighbours.end()) continue;
                        neighbours.push_back(neighbour);
                    }
                    //fprintf(stderr, "neighbours2 merge %d\t%d\n", neighbours2.size(), neighbours.size());
                }
            }
            if (ret.find(cur) == ret.end()) {
                ret[cur] = cluster_counter;
            }
        }
    }
    fprintf(stderr, "Clustering... %f\n", visited.size() * 100.0 / doc_map.size());
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
    int rc = sqlite3_exec(db, "SELECT label_identifier FROM label_names_domains", query_callback_domains, &domains, &zErrMsg);
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
    for (auto& kv : doc_map) {
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

// These two functions handle getting documents in a particular domain
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

    rc = sqlite3_exec(db, "SELECT document_identifier, label FROM label_domains", callback_doc_domains, &ret, &zErrMsg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "SQL Error: %s\n", zErrMsg);
        sqlite3_close(db);
        exit(1);
    }

    return ret;
}

// This produces the forward document_id -> labels map
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

void filter_documents_to_cluster_combo(std::vector<uint64_t> &filtered,
                                       std::vector<uint64_t> combo,
                                       std::map<uint64_t, std::vector<uint64_t>> doc_map) {
    for (auto &kv : doc_map) {
        if(kv.second == combo) {
            filtered.push_back(kv.first);
        }
    }
}

std::map<uint64_t, std::vector<uint64_t>> invert_docid_to_label_map(std::map<uint64_t, std::vector<uint64_t>> &input) {
    std::map<uint64_t, std::vector<uint64_t>> output;
    for (auto &kv : input) {
        for (auto label : kv.second) {
            output[label].push_back(kv.first);
        }
    }
    return output;
}

std::map<uint64_t, uint64_t> cluster(sqlite3 *db, char *src_table, float epsilon, int minpoints) {
    fprintf(stderr, "Fetching domains...\n");
    std::vector<uint64_t> domains = get_domains(db);
    fprintf(stderr, "Generating document id -> domain map...\n");
    std::map<uint64_t, std::vector<uint64_t>> doc_domain_map = generate_doc_domain_map(db);
    // This is a label_identifier -> list of document identifiers mapping
    fprintf(stderr, "Generating document_id -> labels map...\n");
    std::map<uint64_t, std::vector<uint64_t>> doc_idlabel_map = generate_doc_label_map(db, src_table);
    fprintf(stderr, "Inverting to get the label -> document_ids map...\n");
    std::map<uint64_t, std::vector<uint64_t>> doc_labelid_map = invert_docid_to_label_map(doc_idlabel_map);
    fprintf(stderr, "Generating domain combinations...\n");
    std::vector<std::vector<uint64_t>> combos = get_domain_combos(doc_domain_map    );

    std::map<uint64_t, uint64_t> ret;
    unsigned int cluster_counter = 0;
    for (auto combo : combos) {
        std::vector<uint64_t> identifiers;
        std::map<uint64_t, std::vector<uint64_t>> points;
        std::vector<uint64_t> filtered;
        std::list<uint64_t> filtered2;
        int cluster_item_map_offset = 0;
        std::map<uint64_t, uint64_t> cluster_item_map;
        std::list<uint64_t> cluster_items;

        fprintf(stderr, "Filtering documents based on domain...\n");
        filter_documents_to_cluster_combo(filtered, combo, doc_domain_map);

        // Points now contains everything with this combination of domains
        // Now get rid of everything with only one label
        fprintf(stderr, "Filtering documents based on label count...\n");
        for (auto identifier : filtered) {
            auto labels = doc_idlabel_map[identifier];
            if (labels.size() < 2) continue;
            filtered2.push_back(identifier);
        }

        // Now cluster
        fprintf(stderr, "Clustering...\n");
        std::map<const uint64_t, uint64_t> result = dbscan(filtered2, doc_idlabel_map, doc_labelid_map, epsilon, minpoints);
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
            ret.insert(std::pair<uint64_t, uint64_t>(kv.first, mapped_cluster_id));
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

    // Truncate the output table if we've been asked to
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

    // Create the insert query
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
    //  Run the clustering algorithm
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
