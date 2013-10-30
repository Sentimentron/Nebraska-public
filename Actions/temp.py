#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 This file handles temporary path generation.
"""

import os
import logging
import platform 
import tempfile 

def create_sqlite_temp_path():
    if "Linux" in platform.system():
        hnd, tmp = tempfile.mkstemp(suffix='.sqlite', prefix="/dev/shm/") 
    else:
        hnd, tmp = tempfile.mkstemp(suffix='.sqlite', prefix=os.getcwd()+"/") 
    logging.info("SQLite path: %s", tmp)
    return tmp
