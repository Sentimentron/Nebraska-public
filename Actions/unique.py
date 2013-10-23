#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import itertools

class UniqueFilter(object):

    def __init__(self, xml):
        pass

    def execute(self, path, conn):
        c = conn.cursor()
        
        logging.info("Finding duplicate documents...")
        sql = "DELETE FROM input WHERE document IN (SELECT document FROM (SELECT COUNT(*) AS c, document FROM input GROUP BY (document) HAVING c > 1))"
        c.execute(sql)
        
        logging.info("Committing changes...")
        conn.commit()
        return True, conn

class UniqueTextFilter(object):

    def __init__(self, xml):
        pass 
    
    def __filter_nonmatching(self, text):
        parts = text.split(' ')
        parts = filter(lambda x: "http" not in x, parts)
        return ' '.join(parts)
    
    def identical(self, tweet1, tweet2):
        tweet1 = self.__filter_nonmatching(tweet1)
        tweet2 = self.__filter_nonmatching(tweet2)
        return tweet1 == tweet2
    
    def execute(self, path, conn):
        c = conn.cursor()
        # Read in all documents 
        logging.info("Searching for unique tweet text...")
        c.execute("SELECT identifier, document FROM input ORDER BY document")
        documents = []
        for identifier, document_text in c.fetchall():
            documents.append((identifier, document_text))
        
        delete_set = set([])
        for (identifier1, text1), (identifier2, text2) in itertools.izip(documents[0:-2], documents[1:-1]):
            if self.identical(text1, text2):
                delete_set.add(identifier1)
                delete_set.add(identifier2)
        
        logging.info("Deleting documents...")
        sql = "DELETE FROM input WHERE identifier = ?"
        c.executemany(sql, [(identifier,) for identifier in delete_set])

        logging.info("Committing changes...")
        conn.commit()
        
        return True, conn