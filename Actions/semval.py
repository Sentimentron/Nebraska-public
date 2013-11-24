#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import logging

from Actions.db import create_sqlite_label_table
from Actions.label import Labeller

class SemvalInputSource(object):
    """
        Imports documents from the Semval corpus
    """

    def __init__(self, xml):
        self.xml = xml
        self.directory = xml.get("dir")
        self.__assert_directory_exists()

    def __assert_directory_exists(self):
        if not os.path.exists(self.directory):
            raise IOError(
                "SemvalInputSource: directory '%s' does not exist!",
                (self.directory, )
            )

    def get_import_files(self):
        ret = set([])
        # Get suitable files in the directory
        for root, _, files in os.walk(self.directory):
            for filename in files:
                extension = os.path.splitext(filename)[1][1:].strip()
                if extension != "tsv":
                    continue
                ret.add(os.path.join(root, filename))
        return ret

    def execute(self, path, conn):
        create_sqlite_label_table("semval", conn)
        labeller = Labeller("semval")
        input_sources = self.get_import_files()
        conn.text_factory = str
        c = conn.cursor()
        for source in input_sources:
            with open(source,'rb') as csvin:
                csvin = csv.reader(csvin, delimiter='\t')
                next(csvin, None)
                for row in csvin:
                    document = row[3]
                    label = row[2]
                    c.execute(
                        "INSERT INTO input(document) VALUES(?)",
                        (document,)
                    )
                    inserted = c.lastrowid;
                    labeller.associate(inserted, label, conn)

        logging.info("Committing semval input documents...")
        conn.commit()
        return True, conn
