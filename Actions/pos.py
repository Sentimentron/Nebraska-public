#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

class WorkflowNativePOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()

    def execute(self, path, conn):
        # Select the input documents
        c = conn.cursor()
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        # TO DO: Get current tags from the database
        # conn.row_factory = dict_factory
        # c.execute("SELECT identifier, token FROM pos_tokens_%s" % self.dest)
        # tokens = c.fetchall()
        tokens = {}
        for identifier, document in c.fetchall():
            tagged_string = ""
            tagged_form = []
            for token in self.tokenize(document):
                # Check if this this token was in the database already
                if token in tokens:
                    tagged_form.append(tokens[token])
                else:
                    # Insert the new tag in the database
                    c.execute("INSERT INTO pos_tokens_%s(token) VALUES (?)" % self.dest, [token])
                    # Add it to the dictionary
                    tokens[token] = c.lastrowid
                    tagged_form.append(c.lastrowid)
                    #tagged_string = tagged_string + "[" +`tokens[token]`+"] "
            # Convert into tagged string
            tagged_string = ''.join("[%d] " % (t) for t in tagged_form)
            # Insert this string which has been converted into tags into the db
            c.execute("INSERT INTO pos_%s(document_identifier, tokenized_form) VALUES (?, ?)" % self.dest, (identifier, tagged_string))
        logging.info("Committing changes...")
        conn.commit()
        return True, conn

class WhiteSpacePOSTagger(WorkflowNativePOSTagger):

    def tokenize(self, document):
        return document.split(" ")