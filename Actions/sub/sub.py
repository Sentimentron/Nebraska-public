#!/usr/bin/env python

"""
    Dealing with subjective phrase annotation/estimation
"""

import logging

class SubjectivePhraseAnnotator(object):
    """
        Generates subjective phrase annotations.
    """

    def __init__(self, xml):
        """
            Base constructor
        """
        self.output_table = xml.get("outputTable")
        assert self.output_table is not None
        self.sources = set([])
        self.targets = set([])
        for node in xml.iterchildren():
            if node.tag == "DataFlow":
                for subnode in node.iterchildren():
                    if subnode.tag == "Source":
                        self.sources.add(subnode.text)
                    if subnode.tag == "Target":
                        self.targets.add(subnode.text)

    @classmethod
    def generate_filtered_identifiers(cls, sources, conn):
        """
            Lookup document source labels and get the identifiers
        """
        labcursor = conn.cursor()
        sql = "SELECT label_identifier, label FROM label_names_amt"
        labcursor.execute(sql)
        for identifier, name in labcursor.fetchall():
            if name not in sources:
                continue
            idcursor = conn.cursor()
            sql = """SELECT document_identifier
                FROM label_amt WHERE label = ?"""
            idcursor.execute(sql, (identifier,))
            for docid, in idcursor.fetchall():
                yield docid

    def generate_source_identifiers(self, conn):
        """
            Generate identifiers for tweets from files in the <Source /> tags
        """
        logging.debug(self.sources)
        if len(self.sources) == 0:
            return self.get_all_identifiers(conn)
        return self.generate_filtered_identifiers(self.sources, conn)

    def generate_target_identifiers(self, conn):
        """
            Generate identifiers for tweets from files in the <Target /> tags
        """
        if len(self.targets) == 0:
            return self.get_all_identifiers(conn)
        return self.generate_filtered_identifiers(self.targets, conn)

    @classmethod
    def get_all_identifiers(cls, conn):
        """
            No filtering in effect: just get everything from input
        """
        cursor = conn.cursor()
        sql = "SELECT identifier FROM input"
        cursor.execute(sql)
        for row, in cursor:
            yield row

    def generate_annotation(self, tweet):
        """Abstract method"""
        raise NotImplementedError()

    @classmethod
    def generate_output_table(cls, name, conn):
        """Generate annotations table"""
        sql = """CREATE TABLE subphrases_%s (
                    identifier INTEGER PRIMARY KEY,
                    document_identifier INTEGER NOT NULL,
                    annotation TEXT NOT NULL,
                    FOREIGN KEY (identifier) REFERENCES input(identifier)
                    ON DELETE CASCADE
            )""" % (name, )
        logging.debug(sql)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()

    @classmethod
    def insert_annotation(cls, name, identifier, annotation, conn):
        """Insert a generated annotation"""
        cursor = conn.cursor()
        annotation = ' '.join([str(i) for i in annotation])
        sql = """INSERT INTO subphrases_%s
            (document_identifier, annotation)
            VALUES (?, ?)""" % (name, )
        cursor.execute(sql, (identifier, annotation))

    def execute(self, _, conn):
        """Create and insert annotations."""
        self.generate_output_table(self.output_table, conn)
        cursor = conn.cursor()
        sql = """SELECT identifier, document FROM input"""
        cursor.execute(sql)
        target_identifiers = set(self.generate_target_identifiers(conn))
        for identifier, document in cursor.fetchall():
            if identifier not in target_identifiers:
                continue
            annotation = self.generate_annotation(document)
            self.insert_annotation(
                self.output_table, identifier, annotation, conn
            )

        conn.commit()
        return True, conn
