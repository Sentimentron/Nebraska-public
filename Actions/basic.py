#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BasicFilter(object):

    def __init__(self, xml):
        self.string = xml.get("filterText")
    
    def execute(self, path, conn):
        c = conn.cursor()
        sql = "DELETE FROM input WHERE document LIKE ?"
        c.execute(sql, ('%'+self.string+'%',))
        conn.commit()
        return True, conn

class BasicNotFilter(object):
    
    def __init__(self, xml):
        self.string = xml.get("filterText")
    
    def execute(self, path, conn):
        c = conn.cursor()
        sql = "DELETE FROM input WHERE document NOT LIKE ?"
        c.execute(sql, ('%'+self.string+'%',))
        conn.commit()
        return True, conn
