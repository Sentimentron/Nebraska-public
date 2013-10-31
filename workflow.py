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

from Actions import *
from lxml import etree

LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def print_usage_exit():
    logging.error("Incorrect number of arguments")
    logging.info("Usage: workflow.py /path/to/workflow.xml")
    sys.exit(1)

def setup_environment():
    path = os.environ.get("PATH")
    if "Nebraska/Build" not in path:
        logging.error("Nebraska/Build is not in your PATH variable.")
        logging.info("Nebraska/Build contains external compiled programs which aren't part of workflow.py")
        logging.info("Add a line like the following to your ~/.bashrc file:")
        logging.info("\texport PATH=$HOME/Nebraska/Build:$PATH")
        logging.info("Don't forget to restart your shell.")
        sys.exit(1)

def check_gitinfo():
    # Check for untracked files within the tree
    process = subprocess.Popen("git status --porcelain", stdout=subprocess.PIPE, stderr=None, shell=True)
    output, errors = process.communicate()
    changes = False
    for line in output.split("\n"):
        logging.warning("Untracked file present in the tree! (%s)", line)
        changes = True

    # Get the git version
    process = subprocess.Popen("git rev-parse HEAD", stdout=subprocess.PIPE, stderr=None, shell=True)
    output = process.communicate()
    return changes, output[0].strip()


def check_versions():
    # Check that we're in Nebraska's root
    if "Build" not in os.listdir(os.getcwd()):
        logging.error("Nebraska/Build is not in the current directory")
        logging.info("Nebraska/Build contains external compiled programs which aren't part of workflow.py")
        logging.info("To correct this problem, change into the root of Nebraska")
        sys.exit(1)

    # Retrieve the git version
    changes, version = check_gitinfo()

    build_dir = os.path.join(os.getcwd(), "Build")

    for filename in os.listdir(build_dir):
        if filename[0] == '.':
            continue
        filename = os.path.join(build_dir, filename)
        if len(filename) == 0:
            continue
        if os.path.isdir(filename):
            continue
        extension = os.path.splitext(filename)[1][1:]
        if len(extension) > 0:
            continue
        args = [filename, "--version"]
        args = ' '.join(args)
        print args
        pipe = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
        text, err = pipe.communicate()
        if "CHANGES" in text:
            assert changes == True
        tool_version,junk,junk = text.partition('+')
        if version != tool_version:
            raise Exception(("Invalid version", filename, text, version))

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

def get_workflow_task(task_name):
    module_name = "Actions"
    return getattr (
        __import__(module_name, globals(), locals(), [task_name], -1),
        task_name
    )

def execute_workflow(document, sqlite_path):

    # Parse the workflow
    document = etree.fromstring(document)

    #
    # PARSE WORKFLOW OPTIONS

    # Start off with a default set of options
    options = {
        "retain_output" : False,
        "check_untracked": True
    }

    # Retrieve the WorkflowOptions node and update
    x_options = document.find("WorkflowOptions")
    for x_node in x_options.iter():
        if x_node.tag is etree.Comment:
            continue
        if x_node.tag == "WorkflowName":
            options["name"] = x_node.text
        elif x_node.tag == "WorkflowDescription":
            options["description"] = x_node.text
        elif x_node.tag == "RetainOutputFile":
            options["retain_output"] = True
            options["output_file"] = x_node.get("path")
        elif x_node.tag == "DisableUntrackedFileCheck":
            options["check_untracked"] = False

    # Check that the options are correct
    verify_options(options)

    #
    # CREATE TABLES

    # Open a database connection
    sqlite_conn = sqlite.create_sqlite_connection(sqlite_path)

    # Create the tables
    for x_node in document.find("Tables").getchildren():
        if x_node.tag is etree.Comment:
            continue
        if x_node.tag == "TemporaryLabelTable":
            sqlite.create_sqlite_temporary_label_table(x_node.get("name"), sqlite_conn)
        if x_node.tag == "PartOfSpeechTable":
            sqlite.create_sqlite_postables(x_node.get("name"), sqlite_conn)

    #
    # IMPORT SOURCE DATA
    for x_node in document.find("InputSources").getchildren():
        if x_node.tag is etree.Comment:
            continue
        logging.debug(x_node.tag)
        task = get_workflow_task(x_node.tag)
        logging.debug(task)
        task = task(x_node)
        task_status, sqlite_conn = task.execute(sqlite_path, sqlite_conn)

    #
    # APPLY WORKFLOW ACTIONs
    for x_node in document.find("WorkflowTasks").getchildren():
        if x_node.tag is etree.Comment:
            continue
        logging.debug(x_node.tag)
        task = get_workflow_task(x_node.tag)
        logging.debug(task)
        task = task(x_node)
        task_status, sqlite_conn = task.execute(sqlite_path, sqlite_conn)

def read_workflow_file(src):
    # If we've got a workflow file
    if type(src) == sqlite3.Connection:
        # Fetch the XML document stored earlier
        metadata = fetch_metadata("WORKFLOW", db_conn)
        if metadata is None:
            raise Exception("Workflow file has no WORKFLOW metadata key!")
        return metadata
    with open(src, 'r') as src:
        return src.read()

def parse_workflow_sqlite(db_conn):
    metadata = fetch_metadata("WORKFLOW", db_conn)
    if metadata is None:
        raise Exception("Workflow file has no WORKFLOW metadata key!")
    return parse_workflow_xml_doc(etree.fromstring(metadata))

def verify_options(options):
    if options["retain_output"]:
        assert "output_file" in options

def push_workflow_metadata(workflow_file, db_conn):
    with open(workflow_file, 'r') as f:
        content = f.read()
        push_metadata("WORKFLOW", content, db_conn)

    if False:
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

    # Check the tree is up to date, things are in the path
    setup_environment()
    check_versions()

    # Parse command line arguments
    action, workflow_file = parse_arguments()
    assert_workflow_file_exists(workflow_file)

    if action == "touch":
        sqlite_path = sqlite.create_sqlite_temp_path()
        sqlite_conn = sqlite.create_sqlite_connection(sqlite_path)
        sqlite.create_sqlite_input_tables(sqlite_conn)
    else:
        sqlite_path = workflow_file
        sqlite_conn = sqlite.create_sqlite_connection(workflow_file)

    if action == "touch":
        # Push any information we have about the workflow into the database
        push_workflow_metadata(workflow_file, sqlite_conn)

    # Execute the workflow
    workflow = read_workflow_file(workflow_file)
    execute_workflow(workflow, sqlite_path)

if __name__ == "__main__":
    main()