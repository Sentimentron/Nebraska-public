#!/usr/bin/env python

import logging

class TemporaryLabeller(object):
    
    # TemporaryLabellers operate on disposable tables, 
    # label -> identifier mapping typically not retained
    
    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
        
    def execute(self, path, conn):
        # Set up prefix etc
        prefix_table = "temporary_label_%s" % (self.dest,)
        enumeration = {}
        
        # Grab a cursor
        c = conn.cursor()
        
        # Check to see how many items are in the table already 
        logging.debug("Getting label count...")
        sql = "SELECT COUNT(*) FROM %s" % (prefix_table, )
        c.execute(sql)
        for count, in c.fetchall():
            pass 
        logging.debug("%d items found in the table.", count)
        
        # Grab each document 
        logging.info("Labelling documents...")
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        sql = "INSERT INTO %s (document_identifier, label) VALUES (?, ?)" % (prefix_table, )
        for identifier, document in c.fetchall():
            # Split method spits out the parts we want to enumerate 
            for token in set(self.split(document)):
                if token not in enumeration:
                    enumeration[token] = count
                    count += 1
                label_id = enumeration[token]
                c.execute(sql, (identifier, label_id))
         
        # Commit changes
        logging.info("Committing changes...")
        conn.commit()
        return True, conn
         
class HashTagLabeller(TemporaryLabeller):
    
    def split(self, document):
        # Split the document based on spaces
        tokens = document.split(' ')
        tokens = [t for t in tokens if len(t) > 0]
        # Only return those tokens which begin with a hashtag
        return filter(lambda x: x[0] == '#', tokens)

class AtMentionLabeller(TemporaryLabeller):
    
    def split(self, document):
        # Again, just on spaces
        tokens = document.split(' ')
        tokens = [t for t in tokens if len(t) > 0]
        # Only return those tokens which begin with an @
        return filter(lambda x: x[0] == '@', tokens)

class BasicWordLabeller(TemporaryLabeller):
    
    def only_letters(self, word):
        for w in word:
            if w >= 'a' and w <= 'a':
                continue
            if w >= 'A' and w <= 'Z':
                continue 
            return False 
        return True 
    
    def split(self, document):
        tokens = document.split(' ')
        tokens = [t for t in tokens if self.only_letters(t)]
        return tokens