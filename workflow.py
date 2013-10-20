#!/usr/bin/env python

import os 
import sys
import logging
import sqlite3
import tempfile

from Actions import *
from lxml import etree 

LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def retrieve_workflow_file():
	# Check number of parameters
	if len(sys.argv) != 2:
		logging.error("Incorrect number of arguments")
		logging.info("Usage: workflow.py /path/to/workflow.xml")
		sys.exit(1)

	return os.path.abspath(sys.argv[1])

def assert_workflow_file_exists(path):
	if not os.path.exists(path):
		raise IOError("'%s' does not exist" % (path,))

def configure_logging():
	logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

def create_sqlite_temp_path():
	hnd, tmp = tempfile.mkstemp(suffix='.sqlite') 
	logging.info("SQLite path: %s", tmp)
	return tmp

def remove_sqlite_path(path):
	logging.info("Deleting workflow database...")
	os.remove(path)

def create_sqlite_connection(path):
	  logging.info("Opening SQLite database: %s", path)
	  conn = sqlite3.connect(path)
	  logging.debug("Connection open")
	  return conn

def create_sqlite_input_tables(conn):
	# Retrieve a cursor
	c = conn.cursor()
	# Create a table of possible labels
	logging.info("Creating labels...")
	sql = "CREATE TABLE labels (label TEXT UNIQUE)"
	c.execute(sql)
	logging.info("Inserting labels...")
	sql = "INSERT INTO labels (label) VALUES (?)"
	for label in ["Positive", "Negative", "Neutral", "Undefined"]:
		logging.debug("Creating label %s...", label)
		c.execute(sql, (label,))

	# Create a possible domains table 
	logging.info("Creating domains table...")
	sql = "CREATE TABLE domains (domain TEXT UNIQUE)"
	c.execute(sql)
	logging.info("Creating default domain...")
	sql = "INSERT INTO domains (domain) VALUES ('Undefined')";
	c.execute(sql)

	# Create the input table
	logging.info("Creating input table")
	sql = "CREATE TABLE input (identifier INTEGER PIMARY KEY, document TEXT NOT NULL, label TEXT NOT NULL, domain TEXT NOT NULL)"
	c.execute(sql)

	logging.info("Setting up input table triggers...")
	logging.debug("Setting up constraint on label...")
	sql = r"""CREATE TRIGGER input_label_trigger 
	BEFORE INSERT ON input
	FOR EACH ROW
		WHEN (SELECT 1 
			FROM labels 
			WHERE label = new.label
			LIMIT 1) IS NULL
		BEGIN
			SELECT raise(rollback, 'Undefined row label');
		END;"""
	c.execute(sql)

	logging.debug("Setting up constraint on domain...")
	sql = r"""CREATE TRIGGER input_domain_trigger
	BEFORE INSERT ON input
	FOR EACH ROW
		WHEN (SELECT 1 
			FROM domains
			WHERE domain = new.domain
			LIMIT 1) IS NULL
		BEGIN
			SELECT raise(rollback, 'Undefined domain label');
		END;"""
	c.execute(sql)

	logging.info("Creating metadata table...")
	sql = r"""CREATE TABLE metadata (key TEXT UNIQUE, value TEXT)"""
	c.execute(sql)

	logging.info("Committing changes...")
	conn.commit()

def parse_workflow_file(path):
	inputs, filters, special_actions = [], [],  []
	logging.info("Parsing Workflow XML...")
	# Start off with a default set of options 
	options = {
		"retain_input" : False 
	}
	# Parse the top-level document
	document = etree.parse(path)
	# Retrieve the WorkflowOptions node
	x_options = document.find("WorkflowOptions")
	for x_node in x_options.iter():
		if x_node.tag == "WorkflowName":
			options["name"] = x_node.text 
		elif x_node.tag == "WorkflowDescription":
			options["description"] = x_node.text 
	# Retrieve the input sources 
	for x_node in document.find("InputSources").getchildren():
		inputs.append(x_node)
	for x_node in document.find("InputFilters").getchildren():
		filters.append(x_node)
	for x_node in document.find("SpecialActions").getchildren():
		special_actions.append(x_node)
	return inputs, filters, special_actions, options 

def main():
	configure_logging()
	workflow_file = retrieve_workflow_file()
	assert_workflow_file_exists(workflow_file)
	inputs, filters, actions, options = parse_workflow_file(workflow_file)
	try:
		# Set up the SQLite input database 
		sqlite_path = create_sqlite_temp_path()
		sqlite_conn = create_sqlite_connection(sqlite_path)
		create_sqlite_input_tables(sqlite_conn)
		# Import the data using the input sources 
		for i in inputs:
			i = Input(i)
			i.run_import(sqlite_conn)
		# Filter the data 
		for f in filters:
			f = Filter(f)
			f.execute(sqlite_conn)
	finally:
		if not options["retain_input"]:
			remove_sqlite_path(sqlite_path)

if __name__ == "__main__":
	main()