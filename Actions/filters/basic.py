#!/usr/bin/env python

class BasicFilter(object):

	def __init__(self, xml):
		self.string = xml.get("filterText")

	def filtered(self, text):
		return self.string in text