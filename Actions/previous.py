#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import logging
import sqlite3

from db import create_sqlite_connection

class PreviousWorkflow(object):
    
    def __init__(self, xml):
        self.path = xml.get("db")
        if not os.path.exists(self.path):
            raise IOError("PreviousWorkflow: '%s' does not exist!")
        
    def execute(self, path, conn):
        # Close the currently open connection
        logging.debug("Closing existing database...")
        conn.close()
        
        # Copy the existing file over the temporary one
        logging.info("Copying existing output database '%s' to '%s'...", self.path, path)
        shutil.copy(self.path, path)
        
        # Reopen a database connection 
        return True, create_sqlite_connection(path)