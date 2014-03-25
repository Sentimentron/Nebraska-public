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
        count_sql = "SELECT COUNT(*) FROM (%s)" % (sql,)
        cur.execute(count_sql)
        for count, in cur.fetchall():
            pass
        counter = 0
        cur.execute(sql)
        for identifier, text in cur.fetchall():
            print "%.2f %% (%d / %d)" % (counter * 100.0 / count, counter, count)
            counter = counter + 1
            # Retrieve the annotations for this document
            sql = """SELECT annotation FROM subphrases
                        WHERE document_identifier = ?"""
            subcur.execute(sql, (identifier,))
            for annotation, in subcur.fetchall():
                start_point = 0
                for word, a in zip(text.split(' '), annotation):
                    sql = """SELECT identifier, pos, neg, neu, total
                             FROM %s
                             WHERE start == ?
                                AND document_identifier = ?""" % (self.table,)
                    subsubcur.execute(sql, (start_point, identifier))
                    for _id, pos, neg, neu, tot in subsubcur.fetchall():
                        pos = 0 if pos is None else pos
                        neg = 0 if neg is None else neg
                        neu = 0 if neu is None else neu
                        tot = 0 if tot is None else tot
                        if a == 'n':
                            neg += 1
                        elif a == 'e':
                            neu += 1
                        elif a == 'p':
                            pos += 1
                        tot += 1
                        sql = """UPDATE %s SET pos = ?, neg = ?, neu = ?, total = ?
                                    WHERE identifier = ?""" % (self.table,)
                        subsubcur.execute(sql, (pos, neg, neu, tot, _id))
                    start_point += len(word) + 1

        conn.commit()
        return True, conn
