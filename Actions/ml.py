#!/usr/bin/env python

import logging
import subprocess

class ClusterLabeller(object):
    
    def __init__(self, xml):
        
        self.src = xml.get("src")
        self.dest = xml.get("dest")
        self.epsilon = xml.get("epsilon")
        self.min_size = xml.get("minSize")
        
    def execute(self, path, conn):
        # 
        if self.src is None:
            raise ValueError("Must have a src table")
        if self.dest is None:
            raise ValueError("Must have a dest table")
        if self.epsilon is None:
            logging.warning("No epsilon value specified, set at 0.6")
            self.epsilon = 0.6
        if self.min_size is None:
            logging.warning("No minSize value specified, set at 4")
            self.min_size = 4
        
        # 
        args = ["Cluster",
            "--db", path,
            "--src", self.src,
            "--dest", self.dest,
            "--epsilon", self.epsilon,
            "--minpoints", self.min_size,
            "--truncate"
        ]
        args = ' '.join(args)
        subprocess.check_call(args, shell=True)
        
        return True, conn