#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

def fetch_metadata(key, db_conn):
    cur = db_conn.cursor()
    sql = "SELECT value FROM metadata WHERE key = ?"
    cur.execute(sql, (key,))
    for val, in cur.fetchall():
        return val 
    return None

def push_metadata(key, val, db_conn):
    cur = db_conn.cursor()
    if fetch_metadata(key, db_conn) is None:
        sql = "INSERT INTO metadata (key, value) VALUES (?, ?)"
        cur.execute(sql, (key, val))
    else:
        sql = "UPDATE metadata SET value = ? WHERE key = ?"
        cur.execute(sql, (val, key))
    db_conn.commit()
    
def get_git_version():
    # Ask the git process what HEAD's hash is...
    process = subprocess.Popen("git rev-parse HEAD", stdout=subprocess.PIPE, stderr=None, shell=True)
    # Retrieve the response
    output = process.communicate()
    return output[0]