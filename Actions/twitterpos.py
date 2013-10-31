#!/usr/bin/env python
# -*- coding: utf-8 -*-

class GimpelPOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()

    def execute(self, path, conn):
        # Magic Happens Here
        return True, conn

