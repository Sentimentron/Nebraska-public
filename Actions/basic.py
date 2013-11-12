#!/usr/bin/env python
# -*- coding: utf-8 -*-

class BasicFilter(object):

    def __init__(self, xml):
        self.string = xml.get("filterText")
        self.match_pre  = xml.get("matchBefore")
        self.match_post = xml.get("matchAfter")
        if self.match_pre is None:
            self.match_pre = True 
        else: 
            if self.match_pre == "true":
                self.match_pre = True 
            elif self.match_pre == "false":
                self.match_pre = False 
            else:
                raise ValueError(self.match_pre)
        if self.match_post is None:
            self.match_post = True  
        else:
            if self.match_post == "true":
                self.match_post = True 
            elif self.match_post == "false":
                self.match_post = False 
            else:
                raise ValueError(self.match_post)

    def construct_like_string(self):
        like_string = ""
        if self.match_pre:
            like_string = "%"
        like_string += self.string 
        if self.match_post:
            like_string += "%"
        return like_string

    def execute(self, path, conn):
        c = conn.cursor()
        sql = "DELETE FROM input WHERE document LIKE ?"
        like_string = self.construct_like_string()
        c.execute(sql, (like_string,))
        conn.commit()
        return True, conn

class BasicNotFilter(BasicFilter):      
    
    def execute(self, path, conn):
        c = conn.cursor()
        sql = "DELETE FROM input WHERE document NOT LIKE ?"
        like_string = self.construct_like_string()
        c.execute(sql, (like_string,))
        conn.commit()
        return True, conn

class LineBreakFilter(object):

    def __init__(self, xml):
        pass 

    def execute(self, path, conn):
        c = conn.cursor()
        sql = """DELETE FROM input WHERE document LIKE '%
%'"""
        c.execute(sql)
        conn.commit()
        return True, conn