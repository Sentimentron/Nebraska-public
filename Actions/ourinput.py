#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import logging
import unicodedata
from Actions.db import create_sqlite_label_table
from Actions.label import Labeller

class OurInputSource(object):
    """
        Imports documents from our corpus
    """

    def __init__(self, xml):
        self.xml = xml
        self.directory = xml.get("dir")
        self.__assert_directory_exists()

    def __assert_directory_exists(self):
        if not os.path.exists(self.directory):
            raise IOError(
                "OurInputSource: directory '%s' does not exist!",
                (self.directory, )
            )

    def get_import_files(self):
        ret = set([])
        # Get suitable files in the directory
        for root, _, files in os.walk(self.directory):
            for filename in files:
                extension = os.path.splitext(filename)[1][1:].strip()
                if extension != "csv":
                    continue
                ret.add(os.path.join(root, filename))
        return ret

    def execute(self, path, conn):
        create_sqlite_label_table("ours", conn)
        labeller = Labeller("ours")
        input_sources = self.get_import_files()
        conn.text_factory = str
        c = conn.cursor()

        for source in input_sources:
            with open(source,'rb') as csvin:
                csvin = csv.reader(csvin)
                next(csvin, None)
                for row in csvin:
                    labels = {"-2":0, "-1":0, "0":0, "1":0, "2":0}
                    document = row[0]
                    label1 = row[1]
                    labels[label1] +=1
                    label2 = row[2]
                    labels[label2] +=1
                    label3 = row[3]
                    labels[label3] +=1
                    label4 = row[4]
                    labels[label4] +=1
                    label5 = row[5]
                    labels[label5] +=1
                    for key, value in labels.iteritems():
                        if value >= 3:
                            label = key
                            c.execute(
                                "INSERT INTO input(document) VALUES(?)",
                                (document,)
                            )
                            inserted = c.lastrowid;
                            labeller.associate(inserted, label, conn)
                            break

        logging.info("Committing our input documents...")
        conn.commit()
        return True, conn
