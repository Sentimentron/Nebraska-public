#!/usr/bin/env python

import os
import sys
import logging
import subprocess

external_path = os.path.join(os.getcwd(), "External/")

action = None
print sys.argv
if len(sys.argv) != 1:
    action = sys.argv[1]

for root, dirs, files in os.walk(external_path):
    
    old_dir = os.getcwd()
    
    for d in dirs:
        # Determine if a Makefile is present
        path = os.path.join(external_path, d)
        
        makef_path = os.path.join(path, "Makefile")
        
        if not os.path.exists(makef_path):
            logging.warning("No Makefile found for %s", path)
            continue
        
        os.chdir(path)
        
        args = ["make"]
        if action is not None:
            args.append(action)
        args = ' '.join(args)
        logging.warning(args)
        try:
            subprocess.check_call(args, shell=True)
        finally:
            os.chdir(old_dir)
        
    