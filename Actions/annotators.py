#!/usr/bin/env python

"""
    Annotators modify the input table by adding additional columns.
    These columns describe some unique thing about the input document,
    such as its length.
"""

import types
import logging

from sentiwordnet import SentiWordNetReader

class Annotator(object):
    """
        Base, abstract annotator class
    """

    def __init__(self, column_name, column_type):
        """
            Construct the base annotator

            Args:
                column_name: What to call the annotation column
                column_type: Accepted values are Types.FloatType
        """

        if column_type == types.FloatType:
            self.column_type = "FLOAT"
        elif column_type == types.IntType:
            self.column_type = "INTEGER"
        else:
            raise TypeError(column_type)

        self.column_name = column_name

    def create_additional_input_column(self, db_conn):
        """
            Create the additional input column required by this annotator.
        """

        logging.info("Creating annotation column...")
        cursor = db_conn.cursor()
        sql = "ALTER TABLE input ADD COLUMN %s %s" % (
            self.column_name, self.column_type
        )
        logging.debug(sql)
        cursor.execute(sql)
        logging.info("Committing changes...")
        db_conn.commit()

    def execute(self, _, db_conn):
        """
            Produce the annotations using the abstract annotate_doc method
        """

        self.create_additional_input_column(db_conn)

        failed = set([])
        cursor = db_conn.cursor()
        update_sql = "UPDATE input SET %s = ? WHERE identifier = ?" % (
            self.column_name,
        )

        # Read the input documents
        annotation_set = set([])
        cursor.execute("SELECT identifier, document FROM input")
        for row in cursor.fetchall():
            annotation_set.add(row)

        for identifier, text in annotation_set:
            # Annotate each input document
            value = self.produce_annotation(text)
            if value is None:
                failed.add(identifier)
                logging.debug("Annotation failed: %d", identifier)
            # Save the annotation
            cursor.execute(update_sql, (value, identifier))

        if len(failed) != 0:
            logging.info("Failed to annotate %d entries", len(failed))

        logging.info("Committing changes...")
        db_conn.commit()
        return True, db_conn

    def produce_annotation(self, _):
        """
            Abstract stub method
        """
        raise NotImplemented()

class SubjectivityAnnotator(Annotator):
    """
        Annotates tweets with a crude subjectivity score computed
        using SentiWordNet
    """

    def __init__(self, _):
        """
            Constructs the SubjectivityAnnotator, loads SentiWordNet etc.
        """
        super(SubjectivityAnnotator, self).__init__(
            "subjectivity", types.FloatType
        )
        logging.info("Loading SentiWordNet...")
        self.swr = SentiWordNetReader()

    def produce_annotation(self, text):
        """
            Produce an average subjectivity (between 0 and 1) of text
        """
        words = [w.lower() for w in text.split(' ')]
        subjectivity = [self.swr.get_subjectivity(w) for w in words]
        average = [s for s in subjectivity if s != None]

        return sum(average)*1.0/max(len(average), 1.0)
