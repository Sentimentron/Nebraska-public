#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This module contains basic string filtering tasks
"""

class BasicFilter(object):
    """
        BasicFilter deletes any documents which match the filterText

        Attributes:
            string: The string on which to filter
            match_pre: If False, this implies that the filterText must
                appear at the beginning of a matched document.
            match_post: If False, this implies that the filterText must
                appear at the end of a matched document.
    """
    def __init__(self, xml):
        """
            Builds the BasicFilter

            Must have three mandatory XML attributes specified:
                filterText: the string on which to filter
                matchBefore: See match_pre attribute
                matchAfter: See match_post attribute

            Args:
                xml: parsed lxml representation
        """
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
        """
            Internal function which builds the argument
            for the LIKE portion of the query
        """
        like_string = ""
        if self.match_pre:
            like_string = "%"
        like_string += self.string
        if self.match_post:
            like_string += "%"
        return like_string

    def execute(self, _, conn):
        """
            Filters the documents.
        """
        cursor = conn.cursor()
        sql = "DELETE FROM input WHERE document LIKE ?"
        like_string = self.construct_like_string()
        cursor.execute(sql, (like_string,))
        conn.commit()
        return True, conn

class BasicNotFilter(BasicFilter):

    """BasicNotFilter deletes any documents which DON'T match the filterText"""

    def execute(self, _, conn):
        """
        Filters the documents.
        """
        cursor = conn.cursor()
        sql = "DELETE FROM input WHERE document NOT LIKE ?"
        like_string = self.construct_like_string()
        cursor.execute(sql, (like_string,))
        conn.commit()
        return True, conn

class LineBreakFilter(object):

    """
    LineBreakFilter deletes any documents which
    contain line-break ('\n') characters
    """

    def __init__(self, xml):
        """
            This filter takes no XML attributes.
        """
        pass

    def execute(self, _, conn):
        """
            Filters the documents.
        """
        cursor = conn.cursor()
        sql = """DELETE FROM input WHERE document LIKE '%
%'"""
        cursor.execute(sql)
        conn.commit()
        return True, conn
