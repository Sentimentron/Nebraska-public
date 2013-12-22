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

from lxml import etree

from workflow_action_types import WorkflowActionWithOptions

class PreviousWorkflow(WorkflowActionWithOptions):
    
    def __init__(self, xml):
        
        self.path = xml.get("db")
        self.workflow = xml.get("path")

        if self.path is None:
            if self.workflow is None:
                raise ValueError("Need either a path to a DB or Workflow XML file")
            
            with open(self.workflow, 'r') as p:
                workflow = p.read()
            
            # Parse old workflow file to find output location
            document = etree.fromstring(workflow)
            options = document.find("WorkflowOptions")
            for x_node in options.iter():
                if x_node.tag == "RetainOutputFile":
                    self.path = x_node.get("path")
                    break
            
        if self.path is None:
            raise ValueError("Unable to determine a path to a valid database.")
        
        self.strict_hash_check = xml.get("strictHashCheck")
        if self.strict_hash_check is None:
            self.strict_hash_check = False
   
    def __determine_rerun_needed(self, options):
        
        if not options["refresh_output_on_hash_change"]:
            return False

        if "--rerun-everything" in sys.argv:
            return True 
           
        if not os.path.exists(self.path):
            logging.info("Output database doesn't exist")
            return True
        
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
    
    def __rerun(self, old_workflow_path):
        # Run the old workflow
        arg_string = "python workflow.py %s" % (old_workflow_path, )
        logging.debug("Arg string: %s", arg_string)
        subprocess.check_call(arg_string, shell=True)
    
    def rerun(self):
        if not os.path.exists(self.path):
            if self.workflow is None:
                raise Exception("Previous output database doesn't exist, no path given")
            self.__rerun(self.workflow)
            return 
        
        conn = create_sqlite_connection(self.path)
        try:
            
            # Retrieve the old workflow path 
            old_workflow_path = fetch_metadata("WORKFLOW_PATH", conn)
            if not os.path.exists(old_workflow_path):
                raise IOError("WORKFLOw_PATH ('%s') for previous database no longer exists!", old_workflow_path)
            
            self.__rerun(old_workflow_path)
        finally:
            conn.close()
    
    def execute(self, path, conn, options):
        
        if self.__determine_rerun_needed(options):
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
