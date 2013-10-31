#!/usr/bin/env python

import math
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
        
        # Estimate the number of hash functions needed
        logging.info("Estimating number of hash functions needed...")
        sql = """SELECT AVG(c) FROM (
        SELECT COUNT(*) AS c FROM temporary_label_%s
        GROUP BY document_identifier 
        )""" % (self.src,)
        c = conn.cursor()
        c.execute(sql)
        for avg, in c.fetchall():
            pass 
        funcs = 64.0 / avg * math.log(2)
        funcs = int(round(funcs))
        logging.info("Selected %d hash functions.", funcs)
        
        # 
        args = ["Cluster",
            "--db", path,
            "--src", self.src,
            "--dest", self.dest,
            "--epsilon", self.epsilon,
            "--minpoints", self.min_size,
            "--hashfunctions", str(funcs),
            "--truncate"
        ]
        args = ' '.join(args)
        logging.debug(args)
        subprocess.check_call(args, shell=True)
        
        return True, conn