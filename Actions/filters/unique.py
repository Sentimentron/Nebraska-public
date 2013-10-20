#!/usr/bin/env python

import logging

class UniqueFilter(object):

	def is_batch_filter(self):
		return True 

	def __init__(self, xml):
		pass

	def filter(self, db_conn):
		c = db_conn.cursor()
		logging.info("Finding duplicate documents...")
		sql = "SELECT identifier FROM input GROUP BY document HAVING COUNT(*) > 1;"
		c.execute(sql)
		duplicates = 0
		for identifier, in c.fetchall():
			sql = "DELETE FROM input WHERE identifier = ?"
			c.execute(sql, (identifier,))
			duplicates += 1
		logging.info("Committing changes...")
		db_conn.commit()
		logging.info("Found and deleted %d documents...", duplicates)
