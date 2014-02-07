#!/usr/bin/env python

"""
    Contains methods and classes for collecting, summarising
    and outputting experimental results.
"""
import logging
from pyvttbl import DataFrame
_results_objs = {}

def get_result_bucket(name):
    """
        Returns reference to a _ResultCollection.
        Creates it if it doesn't exist
    """
    if name in _results_objs:
        return _results_objs[name]

    _results_objs[name] = DataFrame()
    return _results_objs[name]

def destroy_result_bucket(name):
    """
        Removes references to a _ResultCollection,
        potentially freeing memory.
    """
    if name in _results_objs:
        del _results_objs[name]

class ResultPivotTableOutput(object):

    """
        Handles export of _ResultCollections to LyX-format
        for insertion into final report
    """

    def __init__(self, xml):
        """
            XML configuration looks like this:
            <ResultTableOutput bucket="subjective-anns" file="Tables/Annotations.lyx">
                <Label>tab:annotation</Label>
                <Caption>Comparison of annotation methods</Caption>
                <!--Inside is optional,
                <GroupBy>
                    <Item string="algorithm" />
                </GroupBy>
                <GroupOperation operation="sum" />
            </ResultTableOutput>
        """

        self.fname = xml.get("file")
        self.bucket = xml.get("bucket")
        self.groupby = []
        self.columns = []
        self.where = []
        self.rows = []
        self.target = None
        self.group_operation = 'avg'
        for node in xml.iterchildren():
            if node.tag == "Label":
                self.label = node.text
            if node.tag == "Caption":
                self.caption = node.text
            if node.tag == "Column":
                self.columns.append(node.text)
            if node.tag == "Row":
                self.rows.append(node.text)
            if node.tag == "Target":
                self.target = node.text
            if node.tag == "Where":
                self.where.append(node.text)
            if node.tag == "GroupOperation":
                self.group_operation = node.get("operation")

        if self.target == None:
            raise ValueError((type(self), xml, "Target node missing"))

        if self.group_operation == None:
            raise ValueError((type(self), xml, "Invalid group operation"))


    def execute(self, _, conn):
        """
            Write out a results table 
        """

        df = get_result_bucket(self.bucket)
        pt = df.pivot(self.target, rows=self.rows, 
            cols=self.columns, aggregate=self.group_operation)
        logging.debug(str(pt))

        return True, conn 