#!/usr/bin/env python

"""
    Dealing with subjective phrase annotation/estimation
"""

import re
import logging
from collections import defaultdict
from results import get_result_bucket

class SubjectivePhraseAnnotator(object):
    """
        Generates subjective phrase annotations.
    """

    def __init__(self, output_table):
        """
            Base constructor
        """
        self.output_table = output_table
        assert self.output_table is not None


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
        for identifier, document in cursor.fetchall():
            annotation = self.generate_annotation(document)
            self.insert_annotation(
                self.output_table, identifier, annotation, conn
            )

        conn.commit()
        return True, conn

class EmpiricalSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):
    """
        Probabilistically annotates subjective phases using the
        data given by human annotators
    """
    def __init__(self, xml):
        super(EmpiricalSubjectivePhraseAnnotator, self).__init__(
            xml.get("outputTable")
        )

    def execute(self, _, conn):
        self.generate_output_table(self.output_table, conn)
        cursor = conn.cursor()
        sql = """
            SELECT
                input.identifier, input.document, subphrases.annotation
            FROM input JOIN subphrases
                ON input.identifier = subphrases.document_identifier"""
        cursor.execute(sql)
        annotations = {}
        # Read source annotations
        for identifier, document, annotation in cursor.fetchall():
            if identifier not in annotations:
                annotations[identifier] = []
            annotations[identifier].append(annotation)
        # Compute annotation strings
        for identifier in annotations:
            # Initially zero
            max_len = 0
            for annotation in annotations[identifier]:
                max_len = max(max_len, len(annotation))
            probs = [0.0 for _ in range(max_len)]
            print len(probs)
            for annotation in annotations[identifier]:
                logging.debug((len(annotation), len(probs)))
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            logging.debug(probs)
            # Insert into the database
            self.insert_annotation(self.output_table, identifier, probs, conn)

        conn.commit()
        return True, conn

class FixedSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):
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
        super(FixedSubjectivePhraseAnnotator, self).__init__("")
        # Where are we outputting to?
        self.output_table = xml.get("outputTable")
        if self.output_table is None:
            raise ValueError((type(self), "outputTable must be specified!"))
        # Initialize default items
        self.entries = defaultdict(float)
        self.forward = defaultdict(float)
        self.backward = defaultdict(float)
        # Loop through the children
        for node in xml.iterchildren():
            if node.tag == "EntryNodes":
                for subnode in node.iter():
                    if subnode.tag == "Word":
                        self.insert_entry_term(
                            subnode.get("string"), subnode.get("prob")
                        )
            elif node.tag == "ForwardTransitionNodes":
                for subnode in node.iter():
                    if subnode.tag == "Word":
                        self.insert_forward_transition (
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
        tweet = [t for t in tweet.split(' ') if len(t) > 0]
        ret = [0.0 for _ in range(len(tweet))]
        first = False
        for pos, word in enumerate(tweet):
            # Very crude proper noun filtering
            if word[0].lower() != word[0].lower() and not first:
                continue
            first = False
            ret[pos] += self.entries[word]
            if pos < len(tweet)-1:
                ret[pos + 1] += self.forward[word]
            ret.append(self.entries[word])
        return ret

class SubjectiveAnnotationEvaluator(object):

    def __init__(self, xml):
        self.source = xml.get("sourceTable")
        self.predict = xml.get("predictedTable")
        self.bucket = xml.get("bucket")

        assert self.source is not None
        assert self.predict is not None
        assert self.bucket is not None

    @classmethod
    def calc_mse(cls, annotation1, annotation2):
        annotation1 = [float(i) for i in annotation1.split(' ')]
        annotation2 = [float(i) for i in annotation2.split(' ')]
        return sum([
            (a1 - a2)*(a1 - a2) 
            for a1, a2 
            in zip(annotation1, annotation2)
        ])

    def execute(self, _, conn):
        bucket = get_result_bucket(self.bucket)

        cursor = conn.cursor()
        
        sql = """SELECT subphrases_%s.annotation, subphrases_%s.annotation
            FROM subphrases_%s JOIN subphrases_%s 
            ON subphrases_%s.document_identifier = subphrases_%s.document_identifier"""
        sql = sql % (self.source, self.predict, self.source, 
            self.predict, self.source, self.predict)
        logging.debug(sql)
        cursor.execute(sql)

        for annotation1, annotation2 in cursor.fetchall():
            bucket.insert({"prediction": self.predict, 
                "source": self.source,
                "mse": self.calc_mse(annotation1, annotation2)
            })

        return True, conn 