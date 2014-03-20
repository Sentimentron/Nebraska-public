#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 This file handles temporary path generation and other database ops.
"""

import os
import logging
import sqlite3
import platform
import tempfile

def create_sqlite_temp_path():
    """
        Generates a temporary path to the database file.
    """
    hnd, tmp = tempfile.mkstemp(suffix='.sqlite', prefix=os.getcwd()+"/")
    os.close(hnd)
    logging.info("SQLite path: %s", tmp)
    return tmp

def create_sqlite_connection(path):
    """
        Opens and configures a SQLite connection
    """
    logging.info("Opening SQLite database: %s", path)
    conn = sqlite3.connect(path)
    conn.text_factory = unicode
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA main.page_size = 4096")
    conn.execute("PRAGMA main.cache_size = 5000")
#    conn.execute("PRAGMA main.journal_mode = WAL")
#    conn.execute("PRAGMA main.synchronous = NORMAL")
#   conn.execute("PRAGMA journal_mode = OFF")
    logging.debug("Connection open")
    return conn

def remove_sqlite_path(path):
    """
        Deletes the SQLite database created by a workflow
    """
    logging.info("Deleting workflow database...")
    os.remove(path)

def create_sqlite_temporary_label_table(postfix, conn):
    """
        Temporary labels are used to store labels used for clustering
        and deletion-type things where it's not important for the labels
        to be understood by humans.

        Args:
            postfix: The string appended to 'temporary_label_' for form
            the table's name
            conn: A sqlite3.Connection
    """
    if postfix is None:
        raise ValueError()
    # Retrieve a cursor
    c = conn.cursor()
    # Create the table
    logging.info("Creating temporary label table %s", postfix)
    c.execute(r"""CREATE TABLE temporary_label_%s (
        document_identifier INTEGER NOT NULL,
        label INTEGER NOT NULL
    )""" % (postfix, ))
    logging.debug("Committing temporary table...")
    conn.commit()

def create_sqlite_label_table(name, conn):
    """
        See documentation in label.py
    """
    # Retrieve a cursor
    c = conn.cursor()
    # Create the table which holds the label names
    logging.info("Creating label names table %s...", name)
    c.execute(r"""CREATE TABLE label_names_%s (
    label_identifier INTEGER PRIMARY KEY,
    label TEXT NOT NULL
    )""" % (name, ))
    # Create the table which holds the label names
    logging.info("Creating label table %s...", name)
    c.execute(r"""CREATE TABLE label_%s (
    document_identifier INTEGER NOT NULL,
    label INTEGER NOT NULL,
    FOREIGN KEY (label) REFERENCES label_names_%s(label_identifier)
    ) """ % (name, name))
    logging.debug("Committing temporary table...")
    conn.commit()


def create_sqlite_input_tables(conn):
    """
        Creates a table which holds the input documents.

        Args:
            conn: sqlite3.Connection to the active workflow database
    """
    # Retrieve a cursor
    c = conn.cursor()

    # Create the input table
    logging.info("Creating input table")
    sql = "CREATE TABLE input (identifier INTEGER PRIMARY KEY, document TEXT NOT NULL, date DATETIME)"
    c.execute(sql)

    logging.info("Creating metadata table...")
    sql = r"""CREATE TABLE metadata (key TEXT UNIQUE, value TEXT)"""
    c.execute(sql)

    logging.info("Committing changes...")
    conn.commit()

def create_sqlite_postables(name, conn):
    """
        POS-tagging tables store the tokenized form of documents using two tables:
            1) A table of identifier -> pos_tag tuples ('pos_tokens_%s') which allow humans to decode what's going on
            2) A table of document identifier -> tokenized_form tuples which store the POS-tagged documents
                Each number in a tokenized_form string corresponds to a number within the pos_tokens_%s table.
        Args:
            name: What this POS table is called
            conn: A sqlite3.Connection object
    """
    # Retrieve a cursor
    c = conn.cursor()

    # Create the POSTagging table
    logging.info("Creating pos_%s table", name)
    sql = "CREATE TABLE pos_%s (identifier INTEGER PRIMARY KEY, document_identifier INTEGER, tokenized_form TEXT, FOREIGN KEY(document_identifier) REFERENCES input(identifier) ON DELETE CASCADE)" % (name, )
    c.execute(sql)

    logging.info("Creating pos_tokens_%s table...", name)
    sql = " CREATE TABLE pos_tokens_%s (identifier INTEGER PRIMARY KEY, token TEXT UNIQUE)" % (name, )
    c.execute(sql)

    logging.info("Creating pos_norm_%s table...", name)
    sql = """CREATE TABLE pos_norm_%s (
      document_identifier INTEGER PRIMARY KEY,
      document TEXT,
      FOREIGN KEY (document_identifier) 
        REFERENCES input(identifier) 
          ON DELETE CASCADE)""" % (name, )
    c.execute(sql);

    logging.info("Creating pos_off_%s table...", name) 
    sql = """CREATE TABLE pos_off_%s (
      document_identifier INTEGER,
      start               INTEGER,
      end                 INTEGER,
      word                TEXT,
      tag                 TEXT,
      confidence          FLOAT,
      FOREIGN KEY (document_identifier)
        REFERENCES input(identifier)
          ON DELETE CASCADE)""" % (name,)
    c.execute(sql);

    logging.info("Committing changes...")
    conn.commit()

def create_sqlite_poslisttable(name, src, conn):

    logging.info("Creating pos_list_%s table...", name)
    # Retrieve a cursor
    c = conn.cursor()

    sql = "CREATE TABLE pos_list_%s (pos_identifier INTEGER, FOREIGN KEY (pos_identifier) REFERENCES pos_tokens_%s (identifier) ON DELETE CASCADE)" % (name, src)
    logging.debug(sql)
    c.execute(sql)

    logging.info("Commiting changes...")
    conn.commit()

def create_sqlite_classificationtable(name, conn):
    """
        Classification tables hold the certainty of an classification
        produced by a machine-learning environment such as Weka.
    """

    logging.info("Creating classification_%s table...", name)

    cursor = conn.cursor()
    sql = "CREATE TABLE classification_%s (identifier INTEGER PRIMARY KEY, positive FLOAT, negative FLOAT, FOREIGN KEY (identifier) REFERENCES input (identifier))" % (name, )
    logging.debug(sql)
    cursor.execute(sql)

    logging.info("Committing changes...")
    conn.commit()

def create_labelled_input_table(conn):

    logging.info("Creating labelled input table...")

    cursor = conn.cursor()
    sql = "CREATE TABLE labelled_input (identifier INTEGER PRIMARY KEY, document TEXT NOT NULL, label VARCHAR(200))"
    logging.debug(sql)
    cursor.execute(sql)

    logging.info("Committing changes...")
    conn.commit()

def create_resultstable(conn):

    logging.info("Creating results table...")

    cursor = conn.cursor()
    sql = "CREATE TABLE results (identifier INTEGER PRIMARY KEY, classifier VARCHAR(255) NOT NULL, folds INT NOT NULL, seed INT NOT NULL, correctly_classified_instances INT NOT NULL, incorrectly_classified_instances INT NOT NULL, percent_correctly_classified REAL NOT NULL, percent_incorrectly_classified REAL NOT NULL, mean_absolute_error REAL NOT NULL, root_mean_squared_error REAL NOT NULL, relative_absolute_error REAL NOT NULL, root_relative_squared_error REAL NOT NULL, total_number_of_instances INT NOT NULL, area_under_curve REAL, false_positive_rate REAL, false_negative_rate REAL, f_measure REAL, precision REAL, recall REAL, true_negative_rate REAL, true_positive_rate REAL, train_domain VARCHAR(255), test_domain VARCHAR(255), positive_instances INTEGER, negative_instances INTEGER, neutral_instances INTEGER)"
    logging.debug(sql)
    cursor.execute(sql)

    logging.info("Committing changes...")
    conn.commit()
