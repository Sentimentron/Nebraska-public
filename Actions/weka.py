#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This file's reponsible for running the WEKA workflows
"""

import os
import sys
import logging
import subprocess
import random
from metadata import push_metadata
import csv
from db import create_resultstable

class WekaBenchmark(object):

    def assert_option(self, option, message):
        if self.__dict__[option] is None:
            raise Exception("%s %s" % (option, message))

    def __init__(self, xml):
        # Identifier is for results collation
        self.identifier = xml.get("id")

        # POS table contains the pos tagged forms of tweets
        self.pos_table = xml.get("posSrc")

        # Label table contains the training labels
        self.label_table = xml.get("labelSrc")

        # Number of folds to use
        self.folds = xml.get("folds")

        self.path = xml.get("path")

        # Get or generate a random number seed
        self.seed = xml.get("seed")
        if self.seed is not None:
            self.seed = int(self.seed)
        else:
            self.seed = random.randrange(1,65536)
            logging.info("Setting WekaBenchmark seed as %d...", self.seed)

        # Get the classifier
        self.classifier = xml.get("classifier")

        # Check parameters

        assert self.identifier is not None
        assert self.pos_table is not None
        assert self.label_table is not None
        assert self.folds is not None
        assert self.classifier is not None

        self.folds = int(self.folds)
        assert self.folds > 0

    def execute(self, path, conn):
        if self.path is not None:
            path = self.path

        args = ["WekaBenchmark",
            "-t", path,
            "-T", self.pos_table,
            "-L", self.label_table,
            "-x", str(self.folds),
            "-s", str(self.seed),
            "-W", self.classifier
        ]
        args = ' '.join(args)
        logging.debug(args)
        subprocess.check_call(args, shell=True)
        return True, conn

class WekaCrossDomainBenchmark(WekaBenchmark):
    def execute(self, path, conn):
        args = ["WekaCrossDomainBenchmark",
            "-t", path,
            "-T", self.pos_table,
            "-L", self.label_table,
            "-x", str(self.folds),
            "-s", str(self.seed),
            "-W", self.classifier
        ]
        args = ' '.join(args)
        logging.debug(args)
        subprocess.check_call(args, shell=True)
        return True, conn


class WekaClassify(object):

    def assert_option(self, option, message):
        if self.__dict__[option] is None:
            raise Exception("%s %s" % (option, message))

    def __init__(self, xml):
        # Identifier is for results collation
        self.identifier = xml.get("id")

        # POS table contains the pos tagged forms of tweets
        self.pos_table = xml.get("posSrc")

        # Label table contains the training labels
        self.label_table = xml.get("labelSrc")

        # Label table containing training/test split
        self.training_table = xml.get("splitSrc")

        # Output table
        self.output_table = xml.get("dest")

        # Get or generate a random number seed
        self.seed = xml.get("seed")
        if self.seed is not None:
            self.seed = int(self.seed)
        else:
            self.seed = random.randrange(1,65536)
            logging.info("Setting WekaClassify seed as %d...", self.seed)

        # Get the classifier
        self.classifier = xml.get("classifier")

        # Check parameters

        assert self.identifier is not None
        assert self.pos_table is not None
        assert self.label_table is not None
        assert self.training_table is not None
        assert self.classifier is not None
        assert self.output_table is not None

    def execute(self, path, conn):
        args = ["WekaClassifier",
            "-d", path,
            "-T", self.pos_table,
            "-t", self.training_table,
            "-L", self.label_table,
            "-O", self.output_table,
            "-s", str(self.seed),
            "-W", self.classifier
        ]
        args = ' '.join(args)
        logging.debug(args)
        subprocess.check_call(args, shell=True)
        return True, conn

class WekaBenchmarkExport(object):

    def __init__(self, xml):
        self.output_file = xml.get("name")

    def execute(self, path, conn):
        logging.info("Exporting results to %s" % self.output_file)
        # Retrieve a cursor
        c = conn.cursor()
        sql = "SELECT * FROM results"
        data = c.execute(sql)
        with open(self.output_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['identifier', 'classifier',
             'folds', 'seed', 'correct', 'incorrect',
             'percent correct', 'percent incorrect',
             'mean abs error', 'root mean square error',
             'relative absolute error', 'root relative squared error',
             'total instances', 'area under curve',
             'false positive rate', 'false negative rate',
             'f_measure', 'precision', 'recall', 'true negative rate',
             'true positive rate', 'train domain', 'test domain'])
            writer.writerows(data)
        return True,conn
class WekaResultsExport(object):
    def __init__(self, xml):
        self.input_table = xml.get("table")
        self.output_file = xml.get("file")

    def execute(self, path, conn):
        logging.info("Exporting results to %s" % self.output_file)
        # Retrieve a cursor
        c = conn.cursor()
        sql = "SELECT * FROM classification_%s" % self.input_table
        data = c.execute(sql)
        with open(self.output_file, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['Document ID', 'Positive Confidence', 'Negative Confidence'])
            writer.writerows(data)
        return True,conn
