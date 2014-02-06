#!/usr/bin/env python

"""
    Import Mechanical Turk output files
"""

import os
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

    def execute(self, path, conn):
        """
            Imports an individual MT file into the database.

            If the tweets don't exist in the input table, this will insert them.
            This also inserts sentiment annotations and subjective phrases.
        """
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
                identifier = self.tweet_exists(tweet, conn)
                if identifier is None:
                    logging.debug("Inserting tweet with text '%s'...", tweet)
                    identifier = self.insert_tweet(tweet, conn)
                logging.debug("Tweet identifier: %d", identifier)


class AMTInputSource(object):
    """
        User-facing class for importing our Amazon
         Mechanical Turk corpus format.
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

    def execute(self, path, conn):
        """
            Import configured AMT corpus files into database
        """

        for agent in self.import_agents:
            agent.execute(path, conn)

        return True, conn

