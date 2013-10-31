#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sqlite3
import tempfile

import Actions

def create_sqlite_temp_path():
    return Actions.create_sqlite_temp_path()

def remove_sqlite_path(path):
    logging.info("Deleting workflow database...")
    os.remove(path)

def create_sqlite_connection(path):
    logging.info("Opening SQLite database: %s", path)
    conn = sqlite3.connect(path)
    conn.text_factory = unicode
    conn.execute("PRAGMA foreign_keys = ON;")
    logging.debug("Connection open")
    return conn

def create_sqlite_temporary_label_table(prefix, conn):
    if prefix is None:
        raise ValueError()
    # Retrieve a cursor
    c = conn.cursor()
    # Create the table
    logging.info("Creating temporary label table %s", prefix)
    c.execute(r"""CREATE TABLE temporary_label_%s (
        document_identifier INTEGER NOT NULL,
        label INTEGER NOT NULL
    )""" % (prefix, ))
    logging.debug("Committing temporary table...")
    conn.commit()

def create_sqlite_input_tables(conn):
    # Retrieve a cursor
    c = conn.cursor()

    # Create the input table
    logging.info("Creating input table")
    sql = "CREATE TABLE input (identifier INTEGER PRIMARY KEY, document TEXT NOT NULL)"
    c.execute(sql)

    logging.info("Creating metadata table...")
    sql = r"""CREATE TABLE metadata (key TEXT UNIQUE, value TEXT)"""
    c.execute(sql)

    logging.info("Committing changes...")
    conn.commit()

def create_sqlite_postables(name, conn):
    # Retrieve a cursor
    c = conn.cursor()

    # Create the POSTagging table
    logging.info("Creating pos_%s table" %name)
    sql = "CREATE TABLE pos_%s (identifier INTEGER PRIMARY KEY, document_identifier INTEGER, tokenized_form TEXT, FOREIGN KEY(document_identifier) REFERENCES input(identifier) )" %name
    c.execute(sql)

    logging.info("Creating pos_tokens_%s table..." %name)
    sql = " CREATE TABLE pos_tokens_%s (identifier INTEGER PRIMARY KEY, token TEXT UNIQUE)" %name
    c.execute(sql)

    logging.info("Committing changes...")
    conn.commit()
