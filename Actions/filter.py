#!/usr/bin/env python

import logging
from lxml import etree

class LabelFilter(object):
    
    def __init__(self, xml):
       self.labels = set([])
       
       # Pull out all of the labels we're keeping
       for x_node in xml.getchildren():
           if x_node.tag is etree.Comment:
               continue
           elif x_node.tag == "RetainLabel":
               self.labels.add(int(x_node.get("id")))
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
           
       if len(self.labels) == 0:
           raise ValueError("Need some labels to retain")
    
    def get_table(self):
        # Create the string 
        if self.temporary:
            table = "temporary_label_%s" % (self.table,)
        else:
            table = "label_%s" % (self.table,) 
        return table 
    
    def drop_identifiers(self, cursor):
        table = self.get_table()
        not_portion = ','.join([str(i) for i in self.labels])
        sql = r"""DELETE FROM input WHERE identifier IN (
        SELECT document_identifier FROM %s WHERE label NOT IN (%s)
        );""" % (table, not_portion)
        
        # Execute the query
        logging.debug(sql)
        logging.info("Deleting non-matching documents...")
        cursor.execute(sql)
    
    def execute(self, path, conn):
        
        # Grab a cursor
        c = conn.cursor()
    
        # Delete the documents
        self.drop_identifiers(c)
        
        if self.delete:
            table = self.get_table()
            logging.info("Deleting input table...")
            c.execute("DROP TABLE %s" % (table,))
        
        logging.info("Committing changes...")
        conn.commit()
        
        return True, conn

class HasLabelFilter(LabelFilter):
    
    def __init__(self, xml):
       
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
        