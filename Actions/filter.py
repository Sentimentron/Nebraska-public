#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from lxml import etree

class LabelFilter(object):

    def process_most_popular_labels(self, count):

        # Sanity checks
        assert count is not None
        count = int(count)
        assert count > 0

        self.using_most_popular_labels = True
        self.number_of_popular_labels = count

    def __init__(self, xml):
       self.labels = set([])
       self.using_most_popular_labels = False

       # Pull out all of the labels we're keeping
       for x_node in xml.getchildren():
           if x_node.tag is etree.Comment:
               continue
           elif x_node.tag == "RetainLabel":
               self.labels.add(int(x_node.get("id")))
           elif x_node.tag == "RetainMostPopularLabels":
               self.process_most_popular_labels(x_node.get("count"))
           else:
               raise ValueError((x_node.tag, "Unsupported here"))

       # Known issue: boolean flags aren't translating
       self.table = xml.get("src")
       self.temporary = xml.get("temporary")
       self.delete = xml.get("delete")

       if self.table is None:
           raise ValueError("Need a source table")

       logging.debug(self.temporary)
       if self.temporary is None:
           self.temporary = False
       else:
           self.temporary = True

       if self.delete is None:
           self.delete = False
       else:
           self.delete = True

    def get_table(self):
        # Create the string
        if self.temporary:
            table = "temporary_label_%s" % (self.table,)
        else:
            table = "label_%s" % (self.table,)
        return table

    def drop_identifiers(self, cursor):
        if len(self.labels) == 0:
            raise ValueError("Need some labels to retain")
        table = self.get_table()
        not_portion = ','.join([str(i) for i in self.labels])
        sql = r"""DELETE FROM input WHERE identifier IN (
        SELECT document_identifier FROM %s WHERE label NOT IN (%s)
        );""" % (table, not_portion)

        # Execute the query
        logging.debug(sql)
        logging.info("Deleting non-matching documents...")
        cursor.execute(sql)

    def determine_most_popular_labels(self, cursor):

        assert self.using_most_popular_labels

        # Build query
        sql = "SELECT COUNT(*) AS c, label FROM %s GROUP BY label ORDER BY c DESC LIMIT 0, %d"
        table = self.get_table()

        # Execute query
        cursor.execute(sql % (table, self.number_of_popular_labels))

        for popularity, label in cursor.fetchall():
            logging.debug("Discovered new label '%d' with popularity '%d'", label, popularity)
            yield label

    def execute(self, path, conn):

        # Grab a cursor
        c = conn.cursor()

        # Check if we need to generate any more labels
        if self.using_most_popular_labels:
            logging.info("Determining the %d most popular labels...", self.number_of_popular_labels)
            for label in self.determine_most_popular_labels(c):
                self.labels.add(label)

        # Delete the documents
        self.drop_identifiers(c)

        if self.delete:
            table = self.get_table()
            logging.info("Deleting input table...")
            c.execute("DROP TABLE %s" % (table,))

        logging.info("Vacuuming...")
        c.execute("VACUUM");

        logging.info("Committing changes...")
        conn.commit()

        return True, conn

class HasLabelFilter(LabelFilter):

    def __init__(self, xml):
       self.using_most_popular_labels = False
       # Known issue: boolean flags aren't translating
       self.table = xml.get("src")
       self.temporary = xml.get("temporary")
       self.delete = xml.get("delete")

       if self.table is None:
           raise ValueError("Need a source table")

       logging.debug(self.temporary)
       if self.temporary is None:
           self.temporary = False
       else:
           self.temporary = True

       if self.delete is None:
           self.delete = False
       else:
           self.delete = True

    def drop_identifiers(self, cursor):
        logging.info("Deleting documents which have been labelled...")
        table = self.get_table()
        sql = "DELETE FROM input WHERE identifier IN (SELECT document_identifier FROM %s)" % (table, )
        logging.debug(sql)
        cursor.execute(sql)

class HasNoLabelFilter(HasLabelFilter):

      def drop_identifiers(self, cursor):
        logging.info("Deleting documents which have been labelled...")
        table = self.get_table()
        sql = "DELETE FROM input WHERE identifier NOT IN (SELECT document_identifier FROM %s)" % (table, )
        logging.debug(sql)
        cursor.execute(sql)
