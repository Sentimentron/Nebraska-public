#!/usr/bin/env python

"""
    Contains a class which deals with cross-validating subjectivity
"""

import sys
import logging
import random
import types
import lxml.etree as etree

from collections import defaultdict

class SubjectiveCrossValidationEnvironment(object):

    """
        Cross-validates a given set of subjective phrase annotators
        and stores the results for later printing.
    """

    @classmethod
    def _get_annotator(cls, task_name):
        return getattr (
            __import__("Actions.sub", globals(), locals(), [task_name], -1),
            task_name
        )

    @classmethod
    def _get_human_annotations(cls, conn, document_identifier):
        cursor = conn.cursor()
        sql = """SELECT annotation, sentiment
            FROM subphrases
            WHERE document_identifier = ?"""
        cursor.execute(sql, (document_identifier, ))
        for annotation, sentiment, in cursor.fetchall():
            yield annotation, sentiment

    @classmethod
    def _get_subjectivity_vector(cls, conn, identifier):
        ret = defaultdict(float)
        total_annotations = 0
        for annotation, sentiment in cls._get_human_annotations(conn, identifier):
            total_annotations += 1
            annotation = [i for i in annotation]
            for position, ann in enumerate(annotation):
                if ann not in ['p', 'n', 'e']:
                    continue
                ret[position] += 1.0
        for position in ret:
            ret[position] /= total_annotations
        return [ret[i] for i in sorted(ret)]

    @classmethod
    def _get_document_identifiers(cls, conn):
        cursor = conn.cursor()
        sql = "SELECT identifier FROM input"
        cursor.execute(sql)
        for identifier, in cursor.fetchall():
            yield identifier

    def __init__(self, xml):
        """
            Required attributes are:
                bucket: which result bucket is this ending up as
                folds: how many folds?

            Required contents are:
                Which subjectivity taggers to use, and their parameters.

        """
        # Retrieve the number of folds
        self.fold_count = xml.get("folds")
        assert self.fold_count is not None
        self.fold_count = int(self.fold_count)
        assert self.fold_count > 0

        # Retrieve the results bucket
        self.bucket = xml.get("bucket")
        assert self.bucket is not None

        # Initialise internal taggers list
        self.taggers = []

        # Import and construct each element within this class
        for node in xml.iterchildren():
            if node.tag == etree.Comment:
                continue
            task = self._get_annotator(node.tag)
            task = task(node)
            self.taggers.append((task, etree.tostring(node)))

        # Initialise other stuff
        self.identifiers = None
        self.folds = None
        self.current_table_name = None
        self.results = None

    def generate_folds(self):
        random.shuffle(self.identifiers)
        self.folds = {i:set([]) for i in range(self.fold_count)}
        fold_counter = 0
        for i in self.identifiers:
            self.folds[fold_counter].add(i)
            fold_counter += 1
            fold_counter %= self.fold_count

    def get_source_identifiers(self, current_round, task):
        for r in self.folds:
            if r == current_round:
                continue
            for t in self.folds[r]:
                yield t

    def record_annotation(self, fold, identifier, annotation):
        self.results[fold][identifier] = annotation

    def get_target_identifiers(self, current_round, task):
        return self.folds[current_round]

    def stub_target_table(self, table):
        self.current_table_name = table

    @classmethod
    def pad_annotation(cls, annotation, length):
        """
            Add some '0.0' strings to the annotation until it's
            the right length for the tweet.
        """
        if len(annotation) >= length:
            return annotation
        annotation.extend([0.0 for _ in range(length - len(annotation))])
        return annotation

    @classmethod
    def calc_mse(cls, annotation1, annotation2):
        """
            Calculate the Mean Squared Error for two annotations.
        """
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        assert len(annotation1) == len(annotation2)

        return sum([
            (a1 - a2)*(a1 - a2)
            for a1, a2
            in zip(annotation1, annotation2)
        ])

    def evaluate_fold(self, task, options, r, conn):
        mse_total = 0
        for identifier in self.folds[r]:
            predicted_annotation = self.results[r][identifier]
            actual_annotation = self._get_subjectivity_vector(conn, identifier)
            mse = self.calc_mse(predicted_annotation, actual_annotation)
            mse_total += mse

        print "****CROSS-VALIDATION REPORT****"
        print "Fold: %d of %d" % (r, self.fold_count)
        print "Class: %s" % (type(task), )
        print "MSE: %.4f" % (mse_total,)
        print ""
        print options
        print "*******************************"
        print ""

        return mse_total

    def execute(self, path, conn):

        # Initialise identifiers list and folds
        self.identifiers = [i for i in self._get_document_identifiers(conn)]
        self.generate_folds()

        for task, task_options in self.taggers:
            # Reset the results
            self.results = {r:{} for r in range(self.fold_count)}
            averages = []
            for r in range(self.fold_count):
                task.generate_output_table = types.MethodType(lambda s, y, z: self.stub_target_table(y), task)
                task.generate_source_identifiers = types.MethodType(lambda s, y: self.get_source_identifiers(r, s), task)
                task.generate_target_identifiers = types.MethodType(lambda s, y: self.get_target_identifiers(r, s), task)
                task.insert_annotation = types.MethodType(lambda s, y, z, a, b: self.record_annotation(r, z, a), task)
                task.execute(path, conn)

            for r in range(self.fold_count):
                averages.append(self.evaluate_fold(task, task_options, r, conn))

            print "Overall: %.2f" % (sum(averages) / len(averages))

        return True, conn


