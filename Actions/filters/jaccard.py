# -*- coding: utf-8 -*-
from collections import defaultdict

def dbscan(dataset, distances, epsilon, minimum_points):
    visited = set([])
    unvisited_nodes_left = True
    classification = {}
    cluster_counter = 0
    while len(dataset-visited) > 0:
        unvisited_nodes_left = False
        point = sorted(dataset-visited)[0]
        unvisited_nodes_left = True
        visited.add(point)
        # Should be there for one anoooooother!
        neighbours = dbscan_region_query(point, dataset, epsilon)
        if len(neighbours) < minimum_points:
            for n in neighbours:
                # Classify as noise
                classification[n] = -1
            classification[n] = -1
        # Allocate a new cluster
        c = cluster_counter
        cluster_counter = cluster_counter+1
        # Add point P to that cluster
        classification[point] = c
        # Go through the neighbours and do a range query for them 
        # That's when good neighboooouuurs become... good... frreeeeeeeinds!
        while len(neighbours) != 0: 
            point = sorted(neighbours)[0]
            neighbours.remove(point)
            if point not in visited:
                visited.add(point)
                neighbours_of_p = dbscan_region_query(point, dataset, epsilon)
                if len(neighbours_of_p) >= minimum_points:
                    neighbours = neighbours | neighbours_of_p
            if point not in classification:
                classification[point] = c
                    
    return classification

def _dist(point1, point2):
    u = len(point1 | point2)
    i = len(point1 & point2)
    d = 1.0 - 1.0 * i/u
    return d

def dbscan_region_query(point, dataset, epsilon):
    candidates = set([])
    if type(point) != type(frozenset([])):
        return set([])
    for p in point:
        for d in dataset:
            if p in d:
                candidates.add(d)
    
    return set([d for d in candidates if _dist(point, d) < epsilon])
    

def build_and_run_dbscan(dataset, epsilon, min_points):
    # Build distances set 
    distances = {}
    for point in dataset:
        temp_distance = distances
        for word in sorted(point):
            if word not in temp_distance:
                temp_distance[word] = {}
            temp_distance = temp_distance[word]
    
    # Convert dataset 
    old_dataset = dataset
    dataset = set([])
    for point in old_dataset:
        dataset.add(frozenset(point))
    return dbscan(dataset, distances, epsilon, min_points)

if __name__ == "__main__":
    dataset = [["apples", "bananas", "cranapples"], ["apples", "bananas", "pineapples"], ["apples", "gatorade",  "nigel"], ["apples", "bananas", "lemonade"]]
    
    # Expected, 1 cluster containing first two lists
    # Other list classified as noise
    print build_and_run_dbscan(dataset, 0.6, 2)