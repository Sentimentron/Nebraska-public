#!/usr/bin/env python

"""
    Contains classes used for evaluating subjective phrase
    detection against human input.
"""

import logging

from Actions.results import get_result_bucket
from Actions.sub.sub import SubjectivePhraseAnnotator

class SubjectiveAnnotationEvaluator(object):
    """
        Abstract class which handles getting the appropriate document
        identifiers for subjective phrase detection and saving.
    """
    def __init__(self, xml):
        self.source = xml.get("sourceTable")
        self.predict = xml.get("predictedTable")
        self.bucket = xml.get("bucket")
        self.metric = xml.get("metric")
        if self.metric == None:
            self.metric = "mse"

        assert self.source is not None
        assert self.predict is not None
        assert self.bucket is not None

    @classmethod
    def pad_annotation(cls, annotation, length):
        """
            Add some '0.0' strings to the annotation until it's
            the right length for the tweet.
        """
        if len(annotation) >= length:
            return annotation
        annotation.extend(['0.0' for _ in range(length - len(annotation))])
        return annotation

    @classmethod
    def calc_mse(cls, annotation1, annotation2):
        """
            Calculate the Mean Squared Error for two annotations.
        """
        annotation1 = [i for i in annotation1.split(' ') if len(i) > 0]
        annotation2 = [i for i in annotation2.split(' ') if len(i) > 0]
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        assert len(annotation1) == len(annotation2)
        logging.debug(annotation1)
        logging.debug(annotation2)

        annotation1 = [float(i) for i in annotation1]
        annotation2 = [float(i) for i in annotation2]

        return sum([
            (a1 - a2)*(a1 - a2)
            for a1, a2
            in zip(annotation1, annotation2)
        ])

    @classmethod
    def calc_abs(cls, annotation1, annotation2):
        """
            Reports the annotators ability to correctly identify a word
            which's been highlighted anywhere.
        """
        annotation1 = [float(i) for i in annotation1.split(' ')]
        annotation2 = [float(i) for i in annotation2.split(' ')]
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        result = [
            (i > 0 and j > 0) or (abs(i-0.05) < 0.05 and abs(j-0.05) < 0.05)
            for i, j in zip(annotation1, annotation2)
        ]
        return sum([1-int(i) for i in result])

    def execute(self, _, conn):
        bucket = get_result_bucket(self.bucket)

        cursor = conn.cursor()

        sql = """SELECT subphrases_%s.annotation, subphrases_%s.annotation
            FROM subphrases_%s JOIN subphrases_%s
            ON subphrases_%s.document_identifier
                = subphrases_%s.document_identifier"""
        sql = sql % (self.source, self.predict, self.source,
            self.predict, self.source, self.predict)
        logging.debug(sql)
        cursor.execute(sql)

        for annotation1, annotation2 in cursor.fetchall():
            if self.metric == "mse":
                bucket.insert({"prediction": self.predict,
                    "source": self.source,
                    "mse": self.calc_mse(annotation1, annotation2)
                })
            else:
                bucket.insert({"prediction": self.predict,
                    "source": self.source,
                    "abs": self.calc_abs(annotation1, annotation2)
                })

        return True, conn


class EmpiricalSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):
    """
        Probabilistically annotates subjective phases using the
        data given by human annotators
    """
    def __init__(self, xml):
        super(EmpiricalSubjectivePhraseAnnotator, self).__init__(xml)

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
