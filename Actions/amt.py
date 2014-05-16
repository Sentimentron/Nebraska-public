#!/usr/bin/env python

"""
    Import Mechanical Turk output files
"""

import db
import os
import re
import csv
import logging

from label import Labeller

class _AMTImport(object):
    """
        Imports a specific AMT .csv file.

        Not intended for public conssumption
    """

    def __init__(self, fname):
        """Initialise"""
        self.file = fname
        self.labeller = Labeller("sentiment")
        self.srclabeller = Labeller("amt")

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
            "INSERT INTO input (document, date, source) VALUES (?, datetime(), ?)",
            (tweet, "train")
        )
        return cursor.lastrowid

    @classmethod
    def insert_anns(cls, tweetid, anns, sentiment, conn):
        """
            Insert subjective phrase annotations
        """
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO subphrases (
                document_identifier, annotation, sentiment
            ) VALUES (?, ?, ?)""", (tweetid, anns, sentiment)
        )
        return cursor.lastrowid

    def execute(self, _, conn):
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
                anns = re.sub("[^p|^e|^q|^n]", "q", anns)
                logging.debug(anns)
                self.insert_anns(identifier, anns, sentiment, conn)
                # Insert the sentiment
                logging.debug("Inserting '%s' label...", sentiment)
                self.labeller.associate(identifier, sentiment, conn)
                self.srclabeller.associate(identifier, self.file, conn)

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
                <AMTImportSource dir="MechanicalTurk/" />
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
            ret = set([])

            # Get suitable files in the directory
            for root, _, files in os.walk(self.dir):
                for filename in files:
                    extension = os.path.splitext(filename)[1][1:].strip()
                    if extension != "csv":
                        continue
                    ret.add(os.path.join(root, filename))
            self.files = ret
            self.import_agents = [_AMTImport(f) for f in self.files]

    @classmethod
    def create_subphrase_table(cls, conn):
        """Create a table for subjective phrase annotations"""
        from Actions import db as db
        db.create_subphrase_table(conn)

    def execute(self, path, conn):
        """
            Import configured AMT corpus files into database
        """
        db.create_sqlite_label_table("sentiment", conn)
        db.create_sqlite_label_table("amt", conn)
        self.create_subphrase_table(conn)

        for agent in self.import_agents:
            agent.execute(path, conn)

        conn.commit()
        return True, conn

class AMTNormalise(object):
    def __init__(self, xml):
        """
            You can run this after the AMTInputSource class has been run and it will ensure the only tweets remaining in the database have the majority sentiment label attached to
            them and the subphrase annotation for the tweet is the union of
        """
        self.xml = xml

    def normaliseTweets(self, conn):
        # Pull a list of identifiers from the database for tweets
        cursor = conn.cursor()
        identifiers = cursor.execute("SELECT identifier FROM input")
        # Then pull the four subphrase annotations and the four overall annotations
        for identifier in identifiers:
            cursor2 = conn.cursor()
            # Check if this is from the AMT corpus and if not move on
            # Will be in the subphrases table if it is from the AMT corpus
            check_query = "SELECT COUNT(*) FROM subphrases WHERE document_identifier = ?"
            if cursor2.execute(check_query, (identifier[0],)).fetchone()[0] == 0:
                continue

            query = "SELECT label_names_sentiment.label FROM label_sentiment JOIN label_names_sentiment ON label_sentiment.label = label_names_sentiment.label_identifier WHERE document_identifier = %s" % (identifier)
            sentiments = cursor2.execute(query)
            # Check we got four back and this code assumes four annotations per tweet and if not cry about it. This commented out until I can figure out how to roll the cursor back to the start
            #self.checkNumberOfResults(sentiments, identifier)
            # Compute the majority overall annotation
            overall_sentiment = self.computeOverallSentiment(sentiments, identifier)
            # Delete the instances under this identifier and insert the one new instance
            self.deleteTweet(identifier,conn)
            self.insertTweetsOverallSentiment(identifier[0], overall_sentiment, conn)
            # Union Subphrases
            # Get the 4 subphrase annotations
            query = "SELECT annotation FROM subphrases WHERE document_identifier = ? "
            annotations = cursor2.execute(query, (identifier[0],))
            # Check we got 4 annotations back
            #self.checkNumberOfResults(sentiments, identifier)
            # Work out how many words are in the tweet so we can normalise the length of all the annotations to that
            length = self.getTweetLength(conn, identifier)
            # Normalise the lengths and replace any characters that aren't q,p,e,n with q
            annotations = self.normaliseAnnotations(annotations, length)
            # Now itterate over each character and union it with the others
            annotation = self.unionAnnotations(annotations, length)
            # Now insert this in the database
            self.updateAnnotation(conn, annotation, identifier[0], overall_sentiment)

    def updateAnnotation(self, conn, annotation, identifier, sentiment):
        cursor = conn.cursor()
        query = "DELETE FROM subphrases WHERE document_identifier = ?"
        cursor.execute(query, (identifier,))
        query = "INSERT INTO subphrases(document_identifier, annotation, sentiment) VALUES(?,?,?)"
        cursor.execute(query, (identifier, annotation, sentiment))

    def unionAnnotations(self, annotations, length):
        result = ""
        # For each character in the annotation
        for i in range(0,length):
            res = {}
            res['q'] = 0
            res['p'] = 0
            res['n'] = 0
            res['e'] = 0
            # See what each annotator put
            for annotation in annotations:
                res[annotation[i]] += 1
            # Now the max count is this character in the subphrase. What this means is that p,n,e will always be chosen over q as they come first alphabetically
            # and e will be chosen over p and p over n
            result += self.computeMaxKeyForSubphrases(res)
        return result

    def normaliseAnnotations(self, annotations, length):
        res = set([])
        for annotation in annotations:
            annotation = annotation[0]
            if len(annotation) > length:
                res.add(re.sub("[^p|^n|^e]", "q", annotation[0:length]))
            elif len(annotation) < length:
                for i in range(len(annotation),length):
                    annotation += "q"
                res.add(re.sub("[^p|^n|^e]", "q", annotation))
            else:
                res.add(re.sub("[^p|^n|^e]", "q", annotation))
        return res

    def getTweetLength(self, conn, identifier):
        cursor = conn.cursor()
        tweet = cursor.execute("SELECT document FROM input WHERE identifier=?", (identifier[0],))
        tweet = tweet.fetchone()
        return len(tweet[0].split(" "))

    def deleteTweet(self, identifier, conn):
        cursor = conn.cursor()
        query = "DELETE FROM label_sentiment WHERE document_identifier = %s" % (identifier)
        cursor.execute(query)

    def insertTweetsOverallSentiment(self, identifier, sentiment, conn):
        cursor = conn.cursor()
        query = "INSERT INTO label_sentiment(document_identifier, label) VALUES(?,?)"
        cursor.execute(query, (identifier, self.sentimentStringToDatabaseID(sentiment)))
        query = "UPDATE subphrases SET sentiment = ? WHERE document_identifier = ?"
        cursor.execute(query, (sentiment, identifier))

    def sentimentStringToDatabaseID(self, sentiment):
        vals = {}
        vals['positive'] = 1
        vals['neutral'] = 2
        vals['negative'] = 3
        return vals[sentiment]

    def checkNumberOfResults(self, results, identifier):
        num = 0
        for result in results:
            num += 1
        if num != 4:
            raise ValueError("Never got 4 copies of tweet %s got %d copies" % (identifier, num))

    def computeOverallSentiment(self, sentiments, identifier):
        res = {}
        res['positive'] = 0
        res['negative'] = 0
        res['neutral'] = 0
        for sentiment in sentiments:
            if sentiment[0] == 'positive':
                res['positive'] += 1
            elif sentiment[0] == 'negative':
                res['negative'] += 1
            elif sentiment[0] == 'neutral':
                res['neutral'] += 1
            else:
                raise ValueError("Unknown sentiment %s for tweet %s") % (sentiment[0], identifier[0])
        return self.computeMaxKey(res)

    # In the event of a tie the key which comes first alphabetically is chosen (positive)
    def computeMaxKey(self, d):
             v=list(d.values())
             k=list(d.keys())
             return k[v.index(max(v))]

    def computeMaxKeyForSubphrases(self, d):
        v=list(d.values())
        k=list(d.keys())
        highest = k[v.index(max(v))]
        # We want to give any annotation that appears and is not a q priority over q. So if q has the highest number of appearences but any other letter appears once
        # perfer that letter
        if highest == 'q' and max(v) != 4:
           d['q'] = 0
           v=list(d.values())
           k=list(d.keys())
           highest = k[v.index(max(v))]
        return highest

    def execute(self, path, conn):
        self.normaliseTweets(conn)
        conn.commit()
        return True, conn

