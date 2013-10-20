#!/usr/bin/env python

import os 
import sys
import logging
import sqlite3
import tempfile
import subprocess

from Actions import *
from lxml import etree 

LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def print_usage_exit():
	logging.error("Incorrect number of arguments")
	logging.info("Usage: workflow.py /path/to/workflow.xml")
	sys.exit(1)


def parse_arguments():
	# Check number of parameters
	if not (len(sys.argv) == 2 or len(sys.argv) == 3):
		print_usage_exit()

	action = sys.argv[1]
	if action == "verify":
		if len(sys.argv) != 3:
			print_usage_exit()
		return "verify", os.path.abspath(sys.argv[2])
	elif action == "rerun":
		if len(sys.argv) != 3:
			print_usage_exit()
		return "rerun", os.path.abspath(sys.argv[2])
	else:
		return "touch", os.path.abspath(sys.argv[1])

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
	  conn.text_factory = str 
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
	sql = "CREATE TABLE input (identifier INTEGER PRIMARY KEY, document TEXT NOT NULL, label TEXT NOT NULL, domain TEXT NOT NULL)"
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

def parse_workflow_xml_doc(document):
	inputs, filters, special_actions = [], [],  []
	# Start off with a default set of options 
	options = {
		"retain_output" : False,
		"check_untracked": True
	}
	# Retrieve the WorkflowOptions node
	x_options = document.find("WorkflowOptions")
	for x_node in x_options.iter():
		if x_node.tag == "WorkflowName":
			options["name"] = x_node.text 
		elif x_node.tag == "WorkflowDescription":
			options["description"] = x_node.text 
		elif x_node.tag == "RetainOutputFile":
			options["retain_output"] = True
			options["output_file"] = x_node.get("path")
		elif x_node.tag == "DisableUntrackedFileCheck":
			options["check_untracked"] = False
	# Retrieve the input sources 
	for x_node in document.find("InputSources").getchildren():
		inputs.append(x_node)
	for x_node in document.find("InputFilters").getchildren():
		filters.append(x_node)
	for x_node in document.find("SpecialActions").getchildren():
		special_actions.append(x_node)
	return inputs, filters, special_actions, options 

def parse_workflow_file(path):
	return parse_workflow_xml_doc(etree.parse(path))

def parse_workflow_sqlite(db_conn):
	metadata = fetch_metadata("WORKFLOW", db_conn)
	if metadata is None:
		raise Exception("Workflow file has no WORKFLOW metadata key!")
	return parse_workflow_xml_doc(etree.fromstring(metadata))

def verify_options(options):
	if options["retain_output"]:
		assert "output_file" in options 

def push_workflow_metadata(workflow_file, check_untracked, db_conn):
	with open(workflow_file, 'r') as f:
		content = f.read()
		push_metadata("WORKFLOW", content, db_conn)

	if check_untracked:
		# Check for untracked files within the tree 
		process = subprocess.Popen("git status --porcelain", stdout=subprocess.PIPE, stderr=None, shell=True)
		output, errors = process.communicate()
		for line in output.split("\n"):
			raise Exception("Untracked files present in working tree %s"% (output,))

		# Get the git version 
		process = subprocess.Popen("git rev-parse HEAD", stdout=subprocess.PIPE, stderr=None, shell=True)
		output = process.communicate()
		push_metadata("GIT_HASH", output[0], db_conn)


def main():
	configure_logging()
	action, workflow_file = parse_arguments()
	assert_workflow_file_exists(workflow_file)
	if action == "touch":
		inputs, filters, actions, options = parse_workflow_file(workflow_file)
	elif action == "rerun":
		conn = create_sqlite_connection(workflow_file)
		inputs, filters, actions, options = parse_workflow_sqlite(conn)
		conn.close()
	else:
		raise ValueError("Other operations are not yet supported.")
	try:
		verify_options(options)
		if action == "touch":
			# Set up the SQLite input database 
			sqlite_path = create_sqlite_temp_path()
			sqlite_conn = create_sqlite_connection(sqlite_path)
			create_sqlite_input_tables(sqlite_conn)
		else:
			sqlite_conn = create_sqlite_connection(workflow_file)

		if action == "touch":
			# Push any information we have about the workflow into the database 
			push_workflow_metadata(workflow_file, options["check_untracked"], sqlite_conn) # Need to modify this
		# Import the data using the input sources 
		for i in inputs:
			i = Input(i)
			i.run_import(sqlite_conn)
		# Filter the data 
		for f in filters:
			f = Filter(f)
			f.execute(sqlite_conn)
		sqlite_conn.commit()
		sqlite_conn.close()
	finally:
		if action == "touch":
			if not options["retain_output"]:
				remove_sqlite_path(sqlite_path)
			else:
				output_path = options["output_file"]
				logging.info("Moving temporary database from '%s' to '%s'", sqlite_path, output_path)
				os.rename(sqlite_path, output_path)

if __name__ == "__main__":
	main()