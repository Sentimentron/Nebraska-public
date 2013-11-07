#!/usr/bin/env python

"""
    This file's reponsible for running the WEKA workflows
"""

import os
import sys
import logging
import subprocess
import random
from metadata import push_metadata

class WekaAction(object):

    def assert_option(self, option, message):
        if self.__dict__[option] is None:
            raise Exception("%s %s" % (option, message))

    def __init__(self, xml):
        # Identifier is for results collation
        self.identifier = xml.get("id")

        # POS table contains the pos tagged forms of tweets
        self.pos_table = xml.get("pos-src")

        # Label table contains the training labels
        self.label_table = xml.get("label-src")

        # Number of folds to use
        self.folds = xml.get("folds")

        # Get or generate a random number seed 
        self.seed = xml.get("seed")
        if self.seed is not None:
            self.seed = int(self.seed)
        else:
            self.seed = random.randrange(1,65536)
            logging.info("Setting WekaAction seed as %d...", self.seed)

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
        args = ["WekaClassifiers",
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