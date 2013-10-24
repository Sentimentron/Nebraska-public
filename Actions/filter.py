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
           
    def execute(self, path, conn):
        
        # Grab a cursor
        c = conn.cursor()
        
        # Create the string 
        not_portion = ','.join([str(i) for i in self.labels])
        if self.temporary:
            table = "temporary_label_%s" % (self.table,)
        else:
            table = "label_%s" % (self.table,) 
            
        sql = r"""DELETE FROM input WHERE identifier IN (
        SELECT document_identifier FROM %s WHERE label NOT IN (%s)
        );""" % (table, not_portion)
        
        # Execute the query
        logging.info("Deleting non-matching documents...")
        c.execute(sql)
        
        if self.delete:
            logging.info("Deleting input table...")
            c.execute("DROP TABLE %s" % (table,))
        
        logging.info("Committing changes...")
        conn.commit()
        
        return True, conn