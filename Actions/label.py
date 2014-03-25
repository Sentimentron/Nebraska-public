#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Labellers associate documents with human-readable labels
"""

class Labeller(object):

    """
        Labellers operate on non-temporary table, maintain a seperate
        identity -> label mapping as well as a doc_id -> label mapping.
        Everything that operates on temporary labels should also work.
    """

    def __init__(self, dest):
        """
            Creates the labeller, either using an XML specification
            or a destination specifier
        """

        self.dest = dest
        if self.dest is None:
            raise ValueError()
        self.label_table = "label_%s" % (self.dest, )
        self.names_table = "label_names_%s" % (self.dest,)

    def check_label_exists(self, label_name, db_conn):
        """
            Checks if a label has already been enumerated.
            Args:
                label_name: The label string to check
                db_conn: A sqlite3.Connection object
            Returns:
                True if the label exists, False otherwise
        """
        cursor = db_conn.cursor()
        sql = "SELECT label_identifier FROM %s WHERE label = ?" % (self.names_table,)
        cursor.execute(sql, (label_name,))
        for _, in cursor.fetchall():
            return True
        return False

    def __insert_label(self, label_name, db_conn):
        """
            Internal method which inserts a new label
            name into the database.

            Args:
                label_name: The label to insert
                db_conn: A sqlite3.Connection object
        """
        cursor = db_conn.cursor()
        sql = "INSERT INTO %s (label) VALUES (?)" % (self.names_table)
        cursor.execute(sql, (label_name,))

    def __get_label_id(self, label_name, db_conn):
        """
        Checks if a label has already been enumerated.
        Args:
        label_name: The label string to check
        db_conn: A sqlite3.Connection object
        Returns:
        True if the label exists, False otherwise
        """
        cursor = db_conn.cursor()
        sql = "SELECT label_identifier FROM %s WHERE label = ?" % (self.names_table,)
        cursor.execute(sql, (label_name,))
        for identifier, in cursor.fetchall():
            return identifier
        return None

    def get_label_id(self, label_name, db_conn):
        """
            Checks if a label has already been enumerated (assigned an id),
            and, if it has, a new id is assigned and returned

            Args:
                label_name: The label string to check
                db_conn: A sqlite3.Connection object
            Returns:
                The identifier of the label.
        """
        if self.check_label_exists(label_name, db_conn):
            return self.__get_label_id(label_name, db_conn)

        self.__insert_label(label_name, db_conn)
        return self.get_label_id(label_name, db_conn)

    def associate(self, document_id, label_text, db_conn):
        """
            Assigns a label to a document

            Args:
                document_id: The document identifier to associate the label with
                label_text: The human-readable label name
                db_conn: sqlite3.Connection object
        """

        label_identifier = self.get_label_id(label_text, db_conn)
        if label_identifier is None:
            raise ValueError(label_text)

        cursor = db_conn.cursor()
        sql = "INSERT INTO %s (document_identifier, label) VALUES (?, ?)"
        sql = sql % (self.label_table,)
        cursor.execute(sql, (document_id, label_identifier))
