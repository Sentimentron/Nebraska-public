#!/usr/bin/env python
"""
    Contains functions for matching up POS and subjectivity
"""

import pdb
import logging

class MatchSubjectiveAnnotations(object):
    """
        Inserts what annotations we know into
        the pos_off_ table
    """

    def __init__(self, xml):
        self.sub_table = xml.get("subphrases_table")
        self.table     = xml.get("table")
        self.src_table = xml.get("src_table")
        assert self.table is not None
        assert self.src_table is not None
        assert self.sub_table is not None
        self.table = "pos_off_%s" % (self.table,)
        self.src_table = "pos_norm_%s" % (self.src_table,)

    def execute(self, path, conn):
        pdb.set_trace()
        cur = conn.cursor()
        subcur = conn.cursor()
        subsubcur = conn.cursor()
        # Retrieve all the documents where the POS-normalised version
        # is exactly the same as the original
        sql = """SELECT input.identifier, input.document
                    FROM input JOIN %s
                        ON input.identifier = %s.document_identifier
                    WHERE input.document == %s.document
              """ % (self.src_table, self.src_table, self.src_table)
        cur.execute(sql)
        for identifier, text in cur.fetchall():
            # Retrieve the annotations for this document
            sql = """SELECT annotation FROM subphrases
                        WHERE document_identifier = ?"""
            subcur.execute(sql, (identifier,))
            for annotation, in subcur.fetchall():
                start_point = 0
                for word, a in zip(text.split(' '), annotation):
                    sql = """SELECT identifier, pos, neg, neu
                             FROM %s
                             WHERE start == ?
                                AND document_identifier = ?""" % (self.table,)
                    subsubcur.execute(sql, (start_point, identifier))
                    for _id, pos, neg, neu in subsubcur.fetchall():
                        pos = 0 if pos is None else pos
                        neg = 0 if neg is None else neg
                        neu = 0 if neu is None else neu
                        if a == 'n':
                            neg += 1
                        elif a == 'e':
                            neu += 1
                        elif a == 'p':
                            pos += 1
                        sql = """UPDATE %s SET pos = ?, neg = ?, neu = ?
                                    WHERE identifier = ?""" % (self.table,)
                        subsubcur.execute(sql, (pos, neg, neu, _id))
                    start_point += len(word)

        conn.commit()
        return True, conn
