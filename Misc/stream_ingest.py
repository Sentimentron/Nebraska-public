#!/usr/bin/env python

#
# Nebraska
# Twitter stream database -> sqlite automated conversion script

import os
import sys
import time
import sqlite3
import logging
import datetime
import tempfile
import traceback
import subprocess

import MySQLdb

MYSQL_USER="twitterstream"
MYSQL_PASS="rootfish"
MYSQL_DB="twitterstream"
MYSQL_HOST="localhost"
MYSQL_MIN_COUNT=500

def create_lock_file():
  pass

def remove_lock_file():
  pass

def get_mysql_record_count(connection):
  pass

def create_mysql_connection(user, host password, database):
  logging.info("establishing connection to %s@%s", user, host)
  db = MySQLdb.connection(host=host, user=user, passwd=password, db=database)
  logging.debug("connection established")
  return db

def select_mysql_first_record(connection):
  # Retrieve a cursor
  cur = connection.cursor()
  # Retrieve the first row in the table
  cur.execute("SELECT identifier, date, response FROM stream LIMIT 0,1")
  # Return the first row retrieved
  for identifier, date, response in cur.fetchall():
    return identifier, date, response

def insert_sqlite_record(connection, date, response):
  # Retrieve a cursor
  cur = connection.cursor()
  # Execute an insert query
  cur.execute("insert into stream (date, response) VALUES (?, ?)", (date, response))

def delete_mysql_record(connection, identifier):
  # Retrieve a cursor
  cur = connection.cursor()
  # Delete the row matching the identifier
  cur.execute("DELETE FROM stream WHERE identifier = %d", (identifier,))

def create_sqlite_path():
  tmp = tempfile.mkstemp(suffix='.sqlite') 
  logging.info("sqlite path: %s", tmp)
  return tmp

def create_sqlite_connection(path):
  logging.info("opening sqlite database: %s", path)
  conn = sqlite3.connect(path)
  logging.debug("connection successful")
  return conn

def create_sqlite_tables(connection):
  # Retrieve the cursor 
  c = conn.cursor() 
  # Create the stream table
  logging.debug("Creating stream table...")
  stream_sql = "CREATE TABLE stream (identifier INTEGER PRIMARY KEY, date DATETIME, response TEXT)"
  c.execute(stream_sql)
  logging.debug("Creating metadata table...")
  metadata_sql = "CREATE TABLE metadata (key TEXT, value TEXT)"
  c.execute(metadata_sql)
  # Insert default metadata
  logging.debug("Creating default metadata...")
  default_metadata = "INSERT INTO metadata VALUES ('date_created', CURRENT_TIMESTAMP)"
  c.execute(default_metadata)
  
def close_sqlite(connection):
  connection.close()

def generate_escrow_name():
  tmp = tempfile.mkstemp(suffix='.sqlite.xz', prefix='~/')
  logging.info("generated escrow name: %s", tmp)
  return tmp

def compress_sqlite_to_escrow(temporary_name, escrow_name):
  # Open the destination
  logging.info("opening %s...", escrow_name)  
  fp = open(escrow_name, "w")
  # Compress
  logging.info("Compressing %s", temporary_name)
  subprocess.Popen(["xz", "--stdout", "-z", temporary_name], shell=True, stdout=fp)
  # Delete the old database file
  logging.info("Removing old DB file")
  os.remove(temporary_name)

def handle_critical_exception(ex):
  traceback.print_exc()
  tb = traceback.extract_tb(sys.last_traceback)
  for entry in tb:
    logging.error(str(tb))
  sys.exit(1)

def main():
  # Setup logging to a file in /var/log
  logging.basicConfig(filename="/var/log/stream_ingest.log", level = logging.DEBUG)
  logging.info("Creating lock file...")
  
  # Create the lock file to make sure no other
  # instances of this job are running
  try:
    if not create_lock_file():
      logging.error("Lock creation failure")
      sys.exit(0) # Another job's running concurrently
  except Exception as ex:
    handle_critical_exception(ex)
  
  sqlite_path = create_sqlite_path()

  try:
    # Open connection to mysql database 
    mysql_conn = create_mysql_connection(MYSQL_USER, MYSQL_HOST, MYSQL_PASS, MYSQL_DB)
    # Retrieve the number of waiting mysql records
    mysql_record_count = get_mysql_record_count(mysql_conn)
    logging.info("%d records to transfer", mysql_record_count)
    if mysql_record_count < MYSQL_MIN_COUNT:
      logging.warning("record minimum (%d) not reached", MYSQL_MIN_COUNT)
      return 0
    # Get sqlite database ready for transfer
    sqlite_conn = create_sqlite_connection(sqlite_path)
    create_sqlite_tables(connection)
    sqlite_escrow = generate_escrow_name()
    # Read up to mysql_record_count items out of mysql 
    counter = 0
    while counter < mysql_record_count:
      date, response = select_mysql_first_record(mysql_conn)
      # Insert into sqlite database
      insert_sqlite_record(sqlite_conn, date, response)
      break # Testing 
    # Close sqlite database
    close_sqlite(sqlite_conn)
    # Compress sqlite to escrow 
    compress_sqlite_to_escrow(sqlite_path, sqlite_escrow)
  except Exception as ex:
    handle_critical_exception(ex)
  finally:
    delete_lock_file()
    delete_tmp_db_file(sqlite_path)