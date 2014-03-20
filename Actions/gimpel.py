#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
import sqlite3
import tempfile
import subprocess

import unicodedata

'''
Get all the filtered tweets from the mysql database.
Run the jar on each tweet.

each time we run the jar, parse the stdin for the single tokens.

'''


class GimpelPOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
        self.verbose = xml.get("verbose")
        if self.verbose is None:
            self.verbose = False
        else:
            if self.verbose == "true":
                self.verbose = True
            elif self.verbose == "false":
                self.verbose = False
            else:
                raise ValueError(self.verbose)

    def execute(self, path, conn):
        args = "Gimpel %s input pos_tokens_%s pos_%s pos_off_%s pos_norm_%s" % (path, self.dest, self.dest, self.dest, self.dest)
        subprocess.check_call(args, shell=True)
        return True, conn
