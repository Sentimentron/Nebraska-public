#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This file defines the different Workflow Action types.

    By default, the workflow will call the *execute* method with a sqlite3.Connection
    and a string in case the Workflow action needs a new database connection. These
    functions are expected to return True and the resultant connection object.

    By inheriting from a class defined in here, Actions can request that the Workflow
    gives them different information.

    Summary:
        WorkflowActionWithOptions:
            Specifies that the Workflow should call execute with a third argument
            which contains the options which apply globally.
"""

class WorkflowActionWithOptions(object):

    """
        Specifies that the Workflow should call the execute method with a third
        Dict argument containing the Workflow options.
    """

    def execute(self, connection, path, options):
        """
            Executes the workflow task.
            Raises:
                NotImplementedError on WorkflowActionWithOptions
        """
        raise NotImplementedError((connection, path, options, type(self)))
