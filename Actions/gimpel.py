#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
import sqlite3
import tempfile
import subprocess
import sqlite

'''
Get all the filtered tweets from the mysql database.
Run the jar on each tweet. 

each time we run the jar, parse the stdin for the single tokens. 

'''


class GimpelPOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
            
    def execute(self, path, conn):
        #get tweets from database
        c = conn.cursor()
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        tokens = {}
        List = c.fetchall()
        
        for i in List:
            #run the jar for each i
            output = self.runJar(i)
            
        #Now parse the stdout variable. 
            textArray = output.split("\t")
            #collect all the tags
            tags = textArray[1]
            tagged_form = []
            tagged_string = ""
            for token in tags:
                if token in tokens:
                    tagged_form.append(tokens[token])
                else:
                    c.execute("INSERT INTO pos_tokens_%s(token) VALUES (?)" % self.dest, [token])    
                    tokens[token] = c.lastrowid
                    tagged_form.append(c.lastrowid)
            tagged_string = ''.join("[%d] " % (t) for t in tagged_form)     
            # Insert this string which has been converted into tags into the db
            c.execute("INSERT INTO pos_%s(document_identifier, tokenized_form) VALUES (?, ?)" % self.dest, (identifier, tagged_string))
        conn.commit()
        return True, conn
     
    def runJar(self, tweet):
        #run the jar file for each tweet     
        #p = subprocess.Popen("java -Xmx500m -jar ark-tweet-nlp-0.3.2.jar", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    
        #return iter(p.stdout.readline, b'')
        args = "java -Xmx500m -jar External/ark-tweet-nlp-0.3.2.jar <<< " + tweet
        process = Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout
        #The variables stdout and stderr will be simple strings corresponding to the output from stdout and stderr from the jar. 