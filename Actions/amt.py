#!/usr/bin/env python

"""
    Import Mechanical Turk output files
"""

import os
import re
import csv
import logging

class _AMTImport(object):
    """
        Imports a specific AMT .csv file.

        Not intended for public conssumption
    """

    def __init__(self, fname):
        """Initialise"""
        self.file = fname


    @classmethod
    def tweet_exists(cls, tweet, conn):
        """
            Returns the identifier of a document with identical text to
            tweet if it exists in the database, returns None otherwise.
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT identifier FROM input WHERE document = ?",
            (tweet,)
        )
        for identifier, in cursor.fetchall():
            return identifier

        return None

    @classmethod
    def insert_tweet(cls, tweet, conn):
        """
            Inserts a document with text TWEET and returns the inserted
            identifier
        """
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO input (document, date) VALUES (?, datetime())",
            (tweet,)
        )
        return cursor.lastrowid

    @classmethod
    def insert_anns(cls, anns, tweetid, conn):
        """
            Insert subjective phrase annotations
        """
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO subphrases (
                document_identifier, annotation
            ) VALUES (?, ?)""", (tweetid, anns)
        )
        return cursor.lastrowid

    def execute(self, path, conn):
        """
            Imports an individual MT file into the database.

            If the tweets don't exist in the input table, this will insert them.
            This also inserts sentiment annotations and subjective phrases.
        """
        logging.info("_AMTImport: Importing '%s'...", self.file)
        with open(self.file, 'rU') as inputfp:
            reader = csv.DictReader(inputfp)
            for row in reader:
                tweet = row["Input.tweet"]
                anns = row["Answer.subphrases"]
                sentiment  = row["Answer.sentiment"]
                approve = row["AssignmentStatus"]
                if approve != "Approved":
                    # Don't bother reading stuff that isn't approved
                    continue
                # Associate this tweet with something in the input table
                identifier = self.tweet_exists(tweet, conn)
                if identifier is None:
                    logging.debug(
                        "_AMTImport: Inserting tweet with text '%s'...", tweet
                    )
                    identifier = self.insert_tweet(tweet, conn)
                logging.debug("_AMTImport: Tweet identifier: %d", identifier)
                # Clean an insert subjective phrase annotations
                anns = anns.replace("|", "")
                anns = anns.replace(" ", "")
                anns = re.sub("[^p|^q|^n]", "q", anns)
                logging.debug(anns)
                self.insert_anns(anns, identifier, conn)

class AMTInputSource(object):
    """
        User-facing class for importing our Amazon
         Mechanical Turk corpus format.

         Subjective annotations end up in `subphrases` table

    """
    def __init__(self, xml):
        """
            XML configs look like this"
                <AMTImportSource fname="MechanicalTurk/batch1.csv" />

            This one will import a whole folder:
                <AMTImportSource fname="MechanicalTurk/" />
        """
        self.xml = xml
        self.fname = xml.get("file")
        self.dir = xml.get("dir")

        if self.fname is not None and self.dir is not None:
            raise ValueError((type(self), "file and dir: ambiguous"))

        if self.fname is not None:
            if not os.path.exists(self.fname):
                raise IOError(
                    "AMTImport: file '%s' doesn't exist!" % (self.fname,)
                )
            self.import_agents = [_AMTImport(self.fname)]

        if self.dir is not None:
            if not os.path.exists(self.dir):
                raise IOError(
                    "AMTImport: dir '%s' doesn't exist!" % (self.dir,)
                )
            self.files = os.listdir(self.fname)
            self.import_agents = [_AMTImport(f) for f in self.files]

    @classmethod
    def create_subphrase_table(cls, conn):
        """Create a table for subjective phrase annotations"""
        cursor = conn.cursor()
        sql = r"""CREATE TABLE subphrases (
                identifier          INTEGER PRIMARY KEY,
                document_identifier INTEGER NOT NULL,
                annotation          TEXT NOT NULL,
                FOREIGN KEY (document_identifier)
                REFERENCES input(identifier)
                ON DELETE CASCADE
            )"""
        logging.info("Creating subphrase annotations table...")
        cursor.execute(sql)

    def execute(self, path, conn):
        """
            Import configured AMT corpus files into database
        """
        self.create_subphrase_table(conn)

        for agent in self.import_agents:
            agent.execute(path, conn)

        conn.commit()
        return True, conn

