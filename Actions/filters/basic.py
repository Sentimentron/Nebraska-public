#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BasicFilter(object):

    def __init__(self, xml):
        self.string = xml.get("filterText")

    def filtered(self, text):
        return self.string in text

class BasicNotFilter(object):
    def __init__(self, xml):
        self.string = xml.get("filterText")
        
    def filtered(self, text):
        return self.string not in text
    
    def is_batch_filter(self):
        return True
    
    def filter(self, conn):
        c = conn.cursor()
        sql = "DELETE FROM input WHERE document LIKE ?"
        c.execute(sql, ('%'+self.string+'%',))
        conn.commit()