#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import logging
import snowballstemmer

class Stemmer(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
        self.verbose = xml.get("verbose")
        if self.verbose is None:
            self.verbose = False
        else:
            self.verbose = True
        self.stemmer =  snowballstemmer.stemmer('english')

    def execute(self, path, conn):
        # Select the input documents
        c = conn.cursor()
        sql = "SELECT COUNT(*) FROM input"
        c.execute(sql)
        (number_of_rows, ) = c.fetchone()
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        for counter, (identifier, document) in enumerate(c.fetchall()):
            stemmed = self.stemmer.stemWords(document.lower());
            stemmed = ''.join(stemmed)
            if self.verbose:
                logging.debug("%.2f %% done", counter * 100.0 / number_of_rows)
            c.execute( "UPDATE input SET document = ? WHERE identifier = ?", (stemmed, identifier))
        logging.info("Committing changes...")
        conn.commit()
        return True, conn
