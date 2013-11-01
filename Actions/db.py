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
    if "Linux" in platform.system():
        hnd, tmp = tempfile.mkstemp(suffix='.sqlite', prefix="/dev/shm/") 
    else:
        hnd, tmp = tempfile.mkstemp(suffix='.sqlite', prefix=os.getcwd()+"/") 
    logging.info("SQLite path: %s", tmp)
    return tmp

def create_sqlite_connection(path):
    logging.info("Opening SQLite database: %s", path)
    conn = sqlite3.connect(path)
    conn.text_factory = unicode
    conn.execute("PRAGMA foreign_keys = ON;")
    logging.debug("Connection open")
    return conn