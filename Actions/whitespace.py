#!/usr/bin/env python
# -*- coding: utf-8 -*-

class WhiteSpacePOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

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
            for token in document.split(" "):
                # Check if this this token was in the database already
                if token in tokens:
                    tagged_string = tagged_string + "[" +`tokens[token]`+"] "
                else:
                    # Insert the new tag in the database
                    print tokens
                    c.execute("INSERT INTO pos_tokens_%s(token) VALUES (?)" % self.dest, [token])
                    # Add it to the dictionary
                    tokens[token] = c.lastrowid
                    tagged_string = tagged_string + "[" +`tokens[token]`+"] "
            # Insert this string which has been converted into tags into the db
            c.execute("INSERT INTO pos_%s(document_identifier, tokenized_form) VALUES (?, ?)" % self.dest, (identifier, tagged_string))
        return True, conn

