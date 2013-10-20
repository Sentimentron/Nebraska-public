#!/usr/bin/env python

import logging

class Input(object):

	def __init__(self, xml_tree):
		self.xml_tree = xml_tree 
		logging.debug("Importing input source '%s'", self.xml_tree.tag)
		self._cls_name = self.__import_input_class(self.xml_tree.tag)
		self._class = self._cls_name(xml_tree)

	def run_import(self, db_conn):
		cur = db_conn.cursor()
		logging.info("Importing documents...")
		sql = "INSERT INTO input (document, label, domain) VALUES (?, ?, ?)"
		inserted = 0 
		for text, label, domain in self._class.run_import():
			cur.execute(sql, (text, label, domain))
			inserted += 1
		logging.debug("Committing documents...")
		db_conn.commit()
		logging.info("%d document(s) imported", inserted)

	@classmethod
	def __import_input_class(cls, class_name):

		module_name = "inputs"
		return getattr(
        __import__(module_name, globals(), locals(), [class_name], -1),
        class_name)