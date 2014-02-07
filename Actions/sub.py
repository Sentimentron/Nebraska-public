#!/usr/bin/env python

"""
    Dealing with subjective phrase annotation/estimation
"""

import re
import logging
from collections import defaultdict

class FixedSubjectivePhraseAnnotator(object):

    """
        Annotates subjective phrases according to fixed probability
        tables.
    """

    def insert_entry_term(self, term, prob):
        """Adds a new EntryNode word"""
        self.entries[term] = float(prob)

    def insert_forward_transition(self, term, prob):
        """Adds a ForwardTransition"""
        self.forward[term] = float(prob)

    def insert_backward_transition(self, term, prob):
        """Adds a backward transition"""
        self.backward[term] = float(prob)

    def __init__(self, xml):
        """
            Configurations look like this:
            <FixedSubjectivePhraseAnnotator outputTable="fixed_noprop">
                <EntryNodes>
                    <Word string="bad" prob="1.0" />
                </EntryNodes>
                <ForwardTransitionNodes />
                <BackwardTransitionNodes />
            </FixedSubjectivePhraseAnnotator>
        """
        # Where are we outputting to?
        self.output_table = xml.get("outputTable")
        if self.output_table is None:
            raise ValueError((type(self), "outputTable must be specified!"))
        # Initialize default items
        self.entries = defaultdict(float)
        self.forward = defaultdict(float)
        self.backward = defaultdict(float)
        # Loop through the children
        for node in xml.iter():
            if node.tag == "EntryNodes":
                for subnode in node.iter():
                    if subnode.tag == "Word":
                        self.insert_entry_term(
                            subnode.get("string"), subnode.get("prob")
                        )
            else:
                raise NotImplementedError(node)

    def generate_annotation(self, tweet):
        """
            Generates a list of probabilities that each word
            is annotation
        """
        tweet = re.sub("[^a-zA-Z ]", "", tweet)
        ret = []
        for word in tweet.split(' '):
            # Very crude proper noun filtering
            if word[0].lower() != word[0].lower():
                continue
            ret.append(self.entries[word])


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
        annotation = ' '.join(annotation)
        sql = """INSERT INTO subphrases_%s
            (document_identifier, annotations)
            VALUES (?, ?)""" % (name, )
        cursor.execute(sql, (identifier, annotation))

    def execute(self, _, conn):
        """Create and insert annotations."""
        self.generate_output_table(self.output_table, conn)
        cursor = conn.cursor()
        sql = """SELECT identifier, document FROM input"""
        cursor.execute(sql)
        for identifier, document in cursor.fetchall():
            annotation = self.generate_annotation(document)
            self.insert_annotation(
                self.output_table, identifier, annotation, conn
            )

        conn.commit()
