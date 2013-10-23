#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging 

class Bag(frozenset):
  
  def __init__(self, document_identifier, _iter=[], **kwargs):
      self.identifier = document_identifier
      super(Bag,self).__init__(_iter, **kwargs)
  
  def get_identifier(self):
      return self.identifer

def dbscan(dataset, distances, epsilon, minimum_points):
    visited = set([])
    classification = {}
    cluster_counter = 0
    while len(dataset-visited) > 0:
        logging.debug("DBSCAN progress: %d/%d", len(visited), len(dataset))
        point = sorted(dataset-visited)[0]
        visited.add(point)
        # Should be there for one anoooooother!
        neighbours = dbscan_region_query(point, dataset, epsilon) - visited
        if len(neighbours) < minimum_points:
            classification[point] = -1
            continue
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
                visited.add(point)
            logging.debug("DBSCAN progress: %d/%d", len(visited), len(dataset))
                    
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

class ClusteringJaccardFilter(object):
    
    def __init__(self, xml):
        self.xml = xml
        self.hashtags = False
        self.atmentions = False
        self.use_text = False 
        if xml.get("useHashTags") == "true":
            self.hashtags = True
        if xml.get("useAtMentions") == "true":
            self.atmentions = True
        if xml.get("useText") == "true":
            self.use_text = True 
        if not self.use_text and not self.atmentions and not self.hashtags:
            raise ValueError()
    
    def __build_dataset_entry(self, text):
        parts = filter(lambda x: len(x) > 0, text.split(' '))
        ret = set([])
        if self.hashtags:
            ret.update(filter(lambda x: x[0] == '#', parts))
        if self.atmentions:
            ret.update(filter(lambda x: x[0] == '@', parts))
        if self.use_text:
            ret.update(filter(lambda x: x[0] != '@' and x[0] != '#', parts))
        return frozenset(ret)
    
    def is_batch_filter(self):
        return True 
    
    def filter(self, conn):
        c = conn.cursor()
        c.execute("SELECT identifier, document FROM input")
        dataset = []
        source = []
        logging.info("Extracting clustering terms...")
        for identifier, document_text in c.fetchall():
            d = self.__build_dataset_entry(document_text)
            dataset.append(d)
            source.append((identifier, d))
            
        clusters = build_and_run_dbscan(dataset, 0.6, 1)
        delete_identifiers = set([])
        logging.debug("Identifying documents...")
        for key in clusters:
            
            if clusters[key] == -1:
                continue
            
            for identifier, terms in source:
                if terms == key:
                    delete_identifiers.add(identifier)
         
        logging.info("Deleting documents")
        c.executemany("DELETE FROM input WHERE identifier = ?", [(identifier,) for identifier in delete_identifiers])
        logging.info("Committing changes...")
        conn.commit()

if __name__ == "__main__":
    dataset = [["apples", "bananas", "cranapples"], ["apples", "bananas", "pineapples"], ["apples", "gatorade",  "nigel"], ["apples", "nigel", "lemonade"], ["nigel", "gatorade", "drinking"], ["nigel", "eating", "pudding"]]
    
    # Expected, 1 cluster containing first two lists
    # Other list classified as noise
    print build_and_run_dbscan(dataset, 0.6, 1)