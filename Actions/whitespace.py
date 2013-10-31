#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from pos import WorkflowNativePOSTagger

class WhiteSpacePOSTagger(WorkflowNativePOSTagger):

    def tokenize(self, document):
        return document.split(" ")


