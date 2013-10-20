#!/usr/bin/env python

# Filter factory class 

import logging

class Filter(object):

	def __init__(self, xml_tree):
		self.xml_tree = xml_tree 
		if self.xml_tree.tag != "BasicFilter":
			logging.debug("Importing filter '%s'", self.xml_tree.tag)
			self._cls_name = self.__import_filter_class(self.xml_tree.tag)
			self._class = self._cls_name(xml_tree)
		else:
			self.string = self.xml_tree.get("filterText")

	def execute(self, db_conn):
		# Get a database cursor
		c = db_conn.cursor()

		# Count the number of input documents 
		input_count_original = self.__count_documents(db_conn)
		logging.debug("%d input document(s)", input_count_original)

		if self.xml_tree.tag == "BasicFilter":
			# Ask the import engine to delete everything that doesn't match 
			sql = "DELETE FROM input WHERE document NOT LIKE ?"
			logging.info("Deleting non-matching documents using basic string filtering...")
			c.execute(sql, ("%"+self.string+"%",))
			logging.info("Committing changes...")
			db_conn.commit()
		else:
			# Select the text and identifier of the input documents
			sql = "SELECT identifier, document FROM input;"
			c.execute(sql)
			sql = "DELETE FROM input WHERE identifier = ?"
			for (identifier, text) in c.fetchall():
				if self._class.filtered(text):
					c.execute(sql, (identifier,))
					db_conn.commit()

		# Count the number of output documents 
		input_count_output = self.__count_documents(db_conn)
		logging.debug("%d output document(s)", input_count_output)
		logging.info("Filtered %d document(s)", input_count_original - input_count_output)


	@classmethod 
	def __count_documents(cls, db_conn):
		c = db_conn.cursor()
		# Count the number of input documents 
		logging.debug("Counting input documents...")
		sql = "SELECT COUNT(*) FROM input;"
		c.execute(sql)
		count = 0
		for (count,) in c.fetchall():
			count = count
		return count 

	@classmethod
	def __import_filter_class(cls, class_name):

		module_name = "filters"
		return getattr(
        __import__(module_name, globals(), locals(), [class_name], -1),
        class_name)