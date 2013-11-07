#!/usr/bin/env python

"""

    POS filtering classes

    Sometimes, to stop overfitting, you have to remove or whitelist certain part-of-speech tags. 

    RewritePOSFilter identifies documents with certain POS tags and then rewrites their tokenized form to remove them. 

    WhitelistPOSFilter (unimplemented) adds POS tags to a whitelist table for later input into the classifier

"""

import logging
from lxml import etree

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
        assert self.tag is not None 
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
        query = query % (self.table, like_str)
        logging.debug(query)
        c.execute(query)
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

class POSWhiteListFilter(POSFilter):

    def __init__(self, xml):
        super(POSWhiteListFilter, self).__init__(xml)
        self.dest = xml.get("dest")
        assert self.dest is not None 
        logging.debug("self.dest: %s", self.dest)

    def execute(self, path, conn):

        identifiers = self.identify_pos_tags(conn)
        self.store_whitelist(identifiers, conn)
        return True, conn 

    def store_whitelist(self, identifiers, conn):
        
        logging.info("Writing whitelist...")
        c = conn.cursor()
        sql = "INSERT INTO pos_list_%s VALUES (?)" % (self.dest,)
        logging.debug(sql)
        c.executemany(sql, [(i,) for i in identifiers])

        logging.info("Committing changes...")
        conn.commit()


class POSRewriteFromWhiteList(RewritePOSFilter):

    def __init__(self, xml):
        super(RewritePOSFilter, self).__init__(xml)
        self.ref = xml.get("ref")
        assert self.ref is not None 

    def identify_pos_tags(self, conn):

        c = conn.cursor()
        sql = "SELECT pos_identifier FROM pos_list_%s" % (self.ref,)
        c.execute(sql)

        ret = set([])
        for identifier, in c.fetchall():
            ret.add(identifier)

        return ret 

class POSWhiteListUnpopularTags(POSWhiteListFilter):

    def __init__(self, xml):
        super(POSWhiteListUnpopularTags, self).__init__(xml)

        if xml.get("minPopularity") is None:
            self.min_popularity = 0
        else:
            self.min_popularity = int(xml.get("minPopularity"))

        if xml.get("maxPopularity") is None:
            raise ValueError("maxPopularity must be provided")
        else:
            self.max_popularity = int(xml.get("maxPopularity"))

    def identify_pos_tags(self, conn):
        from collections import Counter 
        c = conn.cursor()

        # Select all the documents available 
        sql = "SELECT tokenized_form FROM pos_%s" % (self.table, )
        c.execute(sql,)

        # Create a popularity counter 
        popularity = Counter([])
        for tokenized_form, in c.fetchall():
            tokens = [int(i) for i in tokenized_form.split(' ')]
            popularity.update(tokens)

        # Find the pos tags which fit the popularity 
        output = set([])
        for token in popularity:
            print token, popularity[token]
            if popularity[token] <= self.max_popularity and popularity[token] > self.min_popularity:
                output.add(token)

        return output