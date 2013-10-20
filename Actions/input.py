#!/usr/bin/env python

import logging
from metadata import *

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
		
		# Get the import files in the source directory 
		import_files = self._class.get_import_files()

		# Get the files already imported 
		already_imported = fetch_metadata("IMPORT_FILES", db_conn)
		if already_imported != None:
			already_imported = set(already_imported.split('|'))
			logging.info("%d documents already imported", len(already_imported))
		else:
			already_imported = set([])

		import_files = import_files - already_imported
		logging.info("%d documents to be imported", len(import_files))
		for text, label, domain in self._class.run_import(import_files):
			cur.execute(sql, (text, label, domain))
			inserted += 1

		push_metadata("IMPORT_FILES", '|'.join(import_files | already_imported), db_conn)
		logging.debug("Committing documents...")
		db_conn.commit()
		logging.info("%d document(s) imported", inserted)

	@classmethod
	def __import_input_class(cls, class_name):

		module_name = "inputs"
		return getattr(
        __import__(module_name, globals(), locals(), [class_name], -1),
        class_name)