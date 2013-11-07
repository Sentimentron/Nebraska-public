#!/usr/bin/env python

"""

    POS filtering classes

    Sometimes, to stop overfitting, you have to remove or whitelist certain part-of-speech tags. 

    RewritePOSFilter identifies documents with certain POS tags and then rewrites their tokenized form to remove them. 

    WhitelistPOSFilter (unimplemented) adds POS tags to a whitelist table for later input into the classifier

"""

import logging

class POSFilter(object):

    def convert_bool(self, raw):
        if raw == "false":
            return False 
        if raw == "true":
            return True 
        raise ValueError(raw)

    def __init__(self, xml):

        # Record the POS tag
        self.tag = xml.get("tag")
        assert self.tag is not None 

        # Record the pos tag table name
        self.table = xml.get("src")
        assert self.table is not None 

        self.match_pre = xml.get("matchBefore") 
        self.match_post = xml.get("matchAfter")

        if self.match_pre is None:
            self.match_pre = True 
        else:
            self.match_pre = self.convert_bool(self.match_pre)
        if self.match_post is None:
            self.match_post = True 
        else:
            self.match_post = self.convert_bool(self.match_pre)

    def identify_pos_tags(self, conn):
        
        logging.info("Matching POS tag '%s'...", self.tag)

        # Build query 
        sql = "SELECT identifier from pos_tokens_%s WHERE token LIKE '%s'" 
        match_str = ''
        if self.match_pre:
            match_str = '%'
        match_str += self.tag 
        if self.match_post:
            match_str += '%'

        # Grab a cursor and execute
        c = conn.cursor()
        c.execute(sql % (self.table, match_str))
        ret = set([])
        for identifier, in c.fetchall():
            ret.add(identifier)

        logging.info("'%d' POS tags matched.", len(ret))
        return ret 

class RewritePOSFilter(POSFilter):

    def rewrite_pos_tag(self, tag_identifier, conn):

        logging.info("Fetching documents with POS tag '%d'...", tag_identifier)

        # Grab a cursor 
        c = conn.cursor()

        # Identify the documents affected 
        document_tuples = set([])
        like_str = "%%%s%%" % (tag_identifier,)
        query = "SELECT identifier, tokenized_form FROM pos_%s WHERE tokenized_form LIKE '%s'" 
        c.execute(query % (self.table, like_str))
        for identifier, tokenized_form in c.fetchall():
            document_tuples.add((identifier, tokenized_form))

        logging.info("%d documents fetched. Rewriting...", len(document_tuples))

        for identifier, tokenized_form in document_tuples:
            tokenized_form = tokenized_form.split(' ')
            tokenized_form = [int(i) for i in tokenized_form]
            tokenized_form = [i for i in tokenized_form if i != tag_identifier]
            tokenized_form = ' '.join([str(i) for i in tokenized_form])
            query = "UPDATE pos_%s SET tokenized_form = ? WHERE identifier = ?" % (self.table, )
            c.execute(query, (tokenized_form, identifier))

        logging.info("Committing changes...")
        conn.commit()

    def execute(self, path, conn):

        # Grab the list of identifiers needed
        pos_identifiers = self.identify_pos_tags(conn)

        # Rewrite the documents which contain each one 
        for i in pos_identifiers:
            self.rewrite_pos_tag(i, conn)

        return True, conn