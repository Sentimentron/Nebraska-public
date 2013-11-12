#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import logging
import sqlite3
import tempfile
import subprocess

import unicodedata

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
        self.verbose = xml.get("verbose")
        if self.verbose is None:
            self.verbose = False
        else:
            if self.verbose == "true":
                self.verbose = True
            elif self.verbose == "false":
                self.verbose = False
            else:
                raise ValueError(self.verbose)

    def execute(self, path, conn):
        #get tweets from database
        c = conn.cursor()
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        token_dict = {}
        rows = c.fetchall()
        for count, (identifier, tagged_string) in enumerate(rows):
            if self.verbose:
                logging.debug("GimpelPOSTagger: %.2f %% done", 100.0*count/len(rows))
            #run the jar for each i
            output = self.runJar(tagged_string)
            #Now parse the stdout variable.
            textArray = output.split("\t")
            #collect all the tags
            tags = textArray[1].split(' ')
            # Get the tokens
            tokens = textArray[0].split(' ')
            tagged_form = []
            tagged_string = ""
            for token, pos_tag in zip(tokens, tags):
                token = "%s/%s" % (token, pos_tag)
                if token in token_dict:
                    tagged_form.append(token_dict[token])
                else:
                    c.execute("INSERT INTO pos_tokens_%s(token) VALUES (?)" % self.dest, [token])
                    token_dict[token] = c.lastrowid
                    tagged_form.append(c.lastrowid)
            tagged_string = ' '.join("%d" % (t) for t in tagged_form)
            # Insert this string which has been converted into tags into the db
            c.execute("INSERT INTO pos_%s(document_identifier, tokenized_form) VALUES (?, ?)" % self.dest, (identifier, tagged_string))
            conn.commit()
        return True, conn

    def runJar(self, tweet):
        #run the jar file for each tweet
        #p = subprocess.Popen("java -Xmx500m -jar ark-tweet-nlp-0.3.2.jar", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #return iter(p.stdout.readline, b'')
        tweet = unicodedata.normalize('NFKD', tweet).encode('ascii', 'ignore')
        args = "java -Xmx500m -jar External/ark-tweet-nlp-0.3.2.jar"
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate(input=tweet)
        return stdout
        #The variables stdout and stderr will be simple strings corresponding to the output from stdout and stderr from the jar.
