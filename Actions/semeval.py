#!/usr/bin/env python
"""
    Contains functions for importing and exporting
    SemEval data
"""

import csv
import pdb
import logging

import Actions.db as db
from Actions.label import Labeller

class SemEvalTaskAImport(object):

    """
        Import SemEval subphrase information
    """

    def __init__(self, xml):
        """
            Required: path - path to the SemEval input
            key = "training" or "test"
        """
        self.path = xml.get("path")
        self.key  = xml.get("key")

        assert self.path is not None
        assert self.key is not None

        self.labeller = Labeller("sem")
        self.sid_labeller = Labeller("sid")
        self.uid_labeller = Labeller("uid")


    def execute(self, _, conn):
        """Import the SemEval stuff"""
        cursor = conn.cursor()

        annotations = {}    # Store provided annotations
        tweets      = {}    # Store provided text
        identifiers = {}

        db.create_sqlite_label_table("sem", conn)
        db.create_sqlite_label_table("sid", conn)
        db.create_sqlite_label_table("uid", conn)
        db.create_subphrase_table(conn)

        counter = 0
        with open(self.path, 'rU') as csv_fp:
            reader = csv.reader(csv_fp, delimiter='\t')

            for line in reader:
                try:
                    uid, sid, start, end, polarity = line[:5]
                    text = '\t'.join(line[5:])
                except ValueError as ex:
                    logging.error(line)
                    raise ex
                if text == "Not Available":
                    continue # Tweet's been removed from Twitter
                identifier = (int(uid), int(sid))
                start = int(start)
                end   = int(end)
                text  = text.decode('utf8')
                assert polarity in ["objective", "positive", "negative", "neutral"]
                tweets[identifier] = text
                if identifier not in annotations:
                    annotations[identifier] = set([])
                annotations[identifier].add((start, end, polarity))

        # Insert the tweets into the database
        for identifier in tweets:
            text = tweets[identifier]
            sql = "INSERT INTO input (document) VALUES (?)"
            cursor.execute(sql, (text,))
            uid, sid = identifier
            identifier = cursor.lastrowid
            identifiers[(uid, sid)] = identifier
            self.labeller.associate(identifier, self.key, conn)
            self.uid_labeller.associate(identifier, uid, conn)
            self.sid_labeller.associate(identifier, sid, conn)

        # Insert the annotations into the database
        for identifier in annotations:
            anns = annotations[identifier]
            text = tweets[identifier]
            insrt = ['q' for i in text.split(' ')]
            # Convert each given annotation
            for start, end, polarity in anns:
                if polarity == "objective":
                    continue
                elif polarity == "negative":
                    polarity = "n"
                elif polarity == "positive":
                    polarity = "p"
                elif polarity == "neutral":
                    polarity = "e"
                for i in range(start, end+1):
                    if i >= len(insrt):
                        break
                    insrt[i] = polarity
            insrt = ''.join(insrt)
            sql = """INSERT INTO subphrases (document_identifier, annotation, sentiment)
                    VALUES (?, ?, 'Unknown')"""
            cursor.execute(sql, (identifiers[identifier], insrt))

        conn.commit()
        return True, conn
