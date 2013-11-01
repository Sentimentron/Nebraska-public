#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
import sqlite3
import subprocess

from metadata import fetch_metadata, get_git_version
from db import create_sqlite_connection

class PreviousWorkflow(object):
    
    def __init__(self, xml):
        self.path = xml.get("db")
        self.strict_hash_check = xml.get("strictHashCheck")
        if self.strict_hash_check is None:
            self.strict_hash_check = False 
   
    def __determine_rerun_needed(self):
        
        if "--rerun-everything" in sys.argv:
            return True 
           
        if not os.path.exists(self.path):
            raise IOError("PreviousWorkflow: '%s' does not exist!")
        
        conn = create_sqlite_connection(self.path)
        try:
            
            if self.strict_hash_check:
                # If the git hashes don't match...
                this_version = get_git_version()
                old_version = fetch_metadata("GIT_HASH", conn)
                if this_version != old_version:
                    logging.info("Hashes indicate that re-run is needed...")
                    return True 
                    
            # Check to see if the old/new versions match
            old_workflow = fetch_metadata("WORKFLOW", conn)
            old_workflow_path = fetch_metadata("WORKFLOW_PATH", conn)
            
            if not os.path.exists(old_workflow_path):
                raise IOError("WORKFLOw_PATH ('%s') for previous database no longer exists!", old_workflow_path)
            
            with open(old_workflow_path, 'r') as old:
                new_workflow = old.read() 
            
            if old_workflow != new_workflow:
                logging.info("Workflow XML mismatch")
                return True
                
            return False 
        finally:
            conn.close()
    
    def rerun(self):
        if not os.path.exists(self.path):
            raise IOError("PreviousWorkflow: '%s' does not exist!")
        
        conn = create_sqlite_connection(self.path)
        try:
            
            # Retrieve the old workflow path 
            old_workflow_path = fetch_metadata("WORKFLOW_PATH", conn)
            if not os.path.exists(old_workflow_path):
                raise IOError("WORKFLOw_PATH ('%s') for previous database no longer exists!", old_workflow_path)
            
            # Run the old workflow
            arg_string = "python workflow.py %s" % (old_workflow_path, )
            logging.debug("Arg string: %s", arg_string)
            subprocess.check_call(arg_string, shell=True)
                
            return False 
        finally:
            conn.close()
    
    def execute(self, path, conn):
        
        if self.__determine_rerun_needed():
            logging.info("Previous workflow needs to be re-run") # Rerun logic goes here
            self.rerun()
        
        # Close the currently open connection
        logging.debug("Closing existing database...")
        conn.close()
        
        # Copy the existing file over the temporary one
        logging.info("Copying existing output database '%s' to '%s'...", self.path, path)
        shutil.copy(self.path, path)
        
        # Reopen a database connection 
        return True, create_sqlite_connection(path)