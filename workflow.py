#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Process a sentiment analysis workflow.

    This file coordinates the activities of Nebraska, reading
      the workflow XML file, creating and setting up databases,
      and importing the appropriate modules to execute the
      workflow.

    Usage: workflow.py /path/to/workflow.xml

"""

import os
import csv
import sys
import shutil
import logging
import sqlite3
import subprocess
import traceback

# from Actions import *
from Actions import db, fetch_metadata, push_metadata, get_git_version, WorkflowActionWithOptions

from lxml import etree

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
options = {}

def print_usage_exit():
    """
        Prints a message on how to use the workflow environment,
        usage and exits with an error code.
    """
    logging.error("Incorrect number of arguments")
    logging.info("Usage: workflow.py /path/to/workflow.xml")
    sys.exit(1)

def setup_environment():
    """
        Checks that the Build/ directory is in the user's path
        and the appropriate JARs are in the CLASSPATH
        Prints an error message if it's not.
    """
    path = os.environ.get("PATH")
    if "Nebraska/Build" not in path:
        logging.error("Nebraska/Build is not in your PATH variable.")
        logging.info(
            "Nebraska/Build contains external compiled "
            "programs which aren't part of workflow.py"
        )
        logging.info("Add a line like the following to your ~/.bashrc file:")
        logging.info("\texport PATH=$HOME/Nebraska/Build:$PATH")
        logging.info("Don't forget to restart your shell.")
        sys.exit(1)

    classpath = os.environ.get("CLASSPATH")
    if "wlsvm.jar" not in classpath:
        logging.error("wlsvm.jar is not in your CLASSPATH variable")
        logging.info(
            "wlsvm.jar provides the WEKA SVM implementation for WekaTest"
        )
        logging.info("Add a line like the following to your ~/.bashrc file:")
        logging.info(
            "\texport CLASSPATH=$HOME/Nebraska/External/wlsvm.jar:$CLASSPATH"
        )
        logging.info("Don't forget to restart your shell")
        exit(1)
    if "libsvm.jar" not in classpath:
        logging.error("libsvm.jar is not in your CLASSPATH variable")
        logging.info(
            "libsvm.jar provides the WEKA SVM implementation for WekaTest"
        )
        logging.info("Add a line like the following to your ~/.bashrc file:")
        logging.info(
            "\texport CLASSPATH=$HOME/Nebraska/External/libsvm.jar:$CLASSPATH"
        )
        logging.info("Don't forget to restart your shell")
        exit(1)


def check_gitinfo():
    """
        Retrieves the current git hash which applies to the files which
        make up the workflow environment.

        Returns:
            A boolean indicating if the working copy is dirty
            The current git hash
    """

    # Check for untracked files within the tree
    process = subprocess.Popen("git status --porcelain",
        stdout=subprocess.PIPE, stderr=None, shell=True
    )
    output, _ = process.communicate()
    changes = False
    for line in output.split("\n"):
        if len(line) == 0:
            continue
        logging.warning("Untracked file present in the tree! (%s)", line)
        changes = True

    # Get the git version
    process = subprocess.Popen("git rev-parse HEAD",
        stdout=subprocess.PIPE, stderr=None, shell=True
    )
    output = process.communicate()

    return changes, output[0].strip()


def check_versions():
    """
        Checks the reported versions of everything in the
        Build/ directory.

        The goal of this method is to avoid unrepeatable results
        by making sure that all of the external tools in the Build/
        directory have been built from the same version of the
        source code that is currently running.

        An external tool is defined as a file within the Build/
        directory without a file extension. Permissions errors
        may occur if files without extensions in that directory
        aren't executable.

        The version is checked by running /path/to/tool --version
        When receiving the --version flag, tools are expected to
        output the git hash they were built from, exit with a
        normal return code, and print no other output.

        Raises:
            Exception: if the reported git hash of the external
            tool is not the same as that of the current tree.
    """
    # Check that we're in Nebraska's root
    if "Build" not in os.listdir(os.getcwd()):
        logging.error(
            "Nebraska/Build is not in the current directory"
        )
        logging.info(
            "Nebraska/Build contains external compiled "
            "programs which aren't part of workflow.py"
        )
        logging.info(
            "To correct this problem, change into the root of Nebraska"
        )
        sys.exit(1)

    # Retrieve the git version
    changes, version = check_gitinfo()
    version = version.strip()

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
        args = [filename.replace(" ", "\\ "), "--version"]
        args = ' '.join(args)
        pipe = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE)
        text, _ = pipe.communicate()
        if "CHANGES" in text:
            assert changes == True
        text = text.strip()
        tool_version, _, _ = text.partition('+')
        tool_version = tool_version.strip()
        if version != tool_version:
            raise Exception(("Invalid version", filename, text, version))

def parse_arguments():
    """
        This method is deprecated.
    """
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
    """
        Stops the workflow if the input file doesn't exist.

        Raises:
            IOError: if the workflow file doesn't exist
    """
    if not os.path.exists(path):
        raise IOError("'%s' does not exist" % (path,))

def configure_logging():
    """
        Sets up the logging format.

        By default, this is logging.DEBUG, but it may be
        too verbose for production environments.
    """
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

def get_workflow_task(task_name):
    """
        Retrieves a workflow task from the Actions/ sub-module.

        Workflow tasks must have an __init__(self, xml) constructor

        Args:
            task_name: The classname of the task to execute
        Returns:
            The imported class from Actions/ with name task_name
        Raises:
            ImportError: if the class doesn't exist?
    """
    module_name = "Actions"
    return getattr (
        __import__(module_name, globals(), locals(), [task_name], -1),
        task_name
    )

def execute_workflow(workflow, workflow_path, sqlite_path):
    """
        Executes an XML workflow file.

        This method parses the WorkflowOptions tag in the workflow,
        verifies that the options are valid, executes the workflow tasks,
        and then optionally moves the output file from its temporary
        location to the RetainOutputFile location specified.

        Args:
            workflow: the XML string which describes the workflow
            workflow_path:
                The path of the workflow file that the workflow
                string came from. This is for metadata.
            sqlite_path:
                Path to the database currently being used.
        Raises:
            Exception if it was not possible to move the output file
            to the specified output

    """

    global options

    # Parse the workflow
    document = etree.fromstring(workflow)

    #
    # PARSE WORKFLOW OPTIONS

    # Start off with a default set of options
    options = {
        "retain_output" : False,
        "check_untracked": True,
        "log_metadata": True,
        "output_count": None,
        "refresh_output_on_hash_change": True
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
        elif x_node.tag == "DebugDocumentCount":
            options["output_count"] = x_node.get("path")

    # Check that the options are correct
    verify_options(options)

    # Try to execute the workflow
    try:
        _execute_workflow(document, sqlite_path, options, workflow_path)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # Print exception details
        print >> sys.stderr, ''.join('\t' + l for l in lines)
    finally:
        if not options["retain_output"]:
            logging.info("Removing output file %s...", sqlite_path)
            os.remove(sqlite_path)
        else:
            try:
                logging.info(
                    "Moving output file from %s to %s...",
                    sqlite_path, options["output_file"]
                )
                shutil.move(sqlite_path, options["output_file"])
            except Exception as ex:
                logging.error("FAILED TO MOVE OUTPUT FILE")
                raise ex

def _execute_workflow(document, sqlite_path, options, workflow_path):
    """
        Internal method called by execute_workflow

        This method copies in the source data, sorts out metadata,
        creates any new tables, and executes the workflow tasks.

        Args:
            document: Parsed workflow XML document
            sqlite_path: Path to the current database
            options: dict containing workflow options
            workflow_path: path to the workflow XML file
        Raises:
            Exception: if something went wrong
    """
    # Open a database connection
    sqlite_conn = db.create_sqlite_connection(sqlite_path)

    #
    # IMPORT SOURCE DATA
    for x_node in document.find("InputSources").getchildren():
        if x_node.tag is etree.Comment:
            continue
        logging.debug(x_node.tag)
        task = get_workflow_task(x_node.tag)
        logging.debug(task)
        task = task(x_node)
        if isinstance(task, WorkflowActionWithOptions):
            _, sqlite_conn = task.execute(sqlite_path, sqlite_conn, options)
        else: 
            _, sqlite_conn = task.execute(sqlite_path, sqlite_conn)

    # Push any information we have about the workflow into the database
    if options["log_metadata"]:
        push_workflow_metadata(workflow_path, sqlite_conn)

    # Create the tables
    for x_node in document.find("Tables").getchildren():
        if x_node.tag is etree.Comment:
            continue
        if x_node.tag == "TemporaryLabelTable":
            db.create_sqlite_temporary_label_table(
                x_node.get("name"), sqlite_conn
            )
        elif x_node.tag == "PartOfSpeechTable":
            db.create_sqlite_postables(
                x_node.get("name"), sqlite_conn
            )
        elif x_node.tag == "PartOfSpeechListTable":
            db.create_sqlite_poslisttable(
                x_node.get("name"), x_node.get("ref"),
                sqlite_conn
            )
        elif x_node.tag == "ClassificationTable":
            db.create_sqlite_classificationtable(
                x_node.get("name"), sqlite_conn
            )
        elif x_node.tag == "ResultsTable":
            db.create_resultstable(sqlite_conn)

    if options["output_count"] is not None:
        output_count = []

    #
    # APPLY WORKFLOW ACTIONS
    for x_node in document.find("WorkflowTasks").getchildren():
        if x_node.tag is etree.Comment:
            continue
        task = get_workflow_task(x_node.tag)
        logging.debug(task)
        task = task(x_node)
        if options["output_count"] is not None:
            output_count.append((count_documents(sqlite_conn), task))
        logging.debug((type(task),isinstance(task,WorkflowActionWithOptions)))
        if isinstance(task, WorkflowActionWithOptions):
            _,sqlite_conn = task.execute(sqlite_path, sqlite_conn, options)
        else:
            _, sqlite_conn = task.execute(sqlite_path, sqlite_conn)

    if options["output_count"] is not None:
        output_count.append((count_documents(sqlite_conn), "FINISH"))
        with open(options["output_count"], "wb") as f:
            writer = csv.writer(f)
            writer.writerow(["count", "activity"])
            writer.writerows(output_count)

def count_documents(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM input")
    for count, in cursor.fetchall():
        logging.info("%d document(s) in the database", count)
        return count

def verify_options(options):
    """
        Verifies whether the options specified in the workflow
        are valid.
    """
    if options["retain_output"]:
        assert "output_file" in options

def push_workflow_metadata(workflow_file, db_conn):
    """
        This method pushes the workflow XML text, path,
        and git hash into the database file for future
        reference.
    """
    logging.debug("Pushing workflow contents...")
    with open(workflow_file, 'r') as workflow_fp:
        content = workflow_fp.read()
        push_metadata("WORKFLOW", content, db_conn)

    # Push the path of the workflow file
    push_metadata("WORKFLOW_PATH", workflow_file, db_conn)

    # Get the git version
    logging.debug("Pushing workflow version...")
    git_hash = get_git_version()
    push_metadata("GIT_HASH", git_hash, db_conn)

    if False:
        # Check for untracked files within the tree
        process = subprocess.Popen(
            "git status --porcelain", stdout=subprocess.PIPE,
            stderr=None, shell=True
        )
        output, _ = process.communicate()
        for _ in output.split("\n"):
            raise Exception(
                "Untracked files present in working tree %s"% (output,)
            )
def read_workflow_file(src):
    """
        Reads the the workflow information either from a file, or
        from a database output previously by another workflow.

        Args:
            src: Either a sqlite3.Connection or a string representing a path
        Raises:
            Exception: if the workflow database has corrupt metadata
    """
    # If we've got a workflow file
    if type(src) == sqlite3.Connection:
        # Fetch the XML document stored earlier
        metadata = fetch_metadata("WORKFLOW", src)
        if metadata is None:
            raise Exception("Workflow file has no WORKFLOW metadata key!")
        return metadata
    with open(src, 'r') as src:
        return src.read()

def main():
    """Entrypoint for the Workflow system"""
    configure_logging()

    # Check the tree is up to date, things are in the path
    setup_environment()
    #check_versions()

    # Parse command line arguments
    action, workflow_file = parse_arguments()
    assert_workflow_file_exists(workflow_file)

    if action == "touch":
        sqlite_path = db.create_sqlite_temp_path()
        sqlite_conn = db.create_sqlite_connection(sqlite_path)
        db.create_sqlite_input_tables(sqlite_conn)
    else:
        sqlite_path = workflow_file
        sqlite_conn = db.create_sqlite_connection(workflow_file)

    # Execute the workflow
    workflow = read_workflow_file(workflow_file)
    execute_workflow(workflow, workflow_file, sqlite_path)

if __name__ == "__main__":
    main()
