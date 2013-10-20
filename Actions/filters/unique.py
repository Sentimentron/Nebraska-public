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
		sql = "DELETE FROM input WHERE document IN (SELECT document FROM (SELECT COUNT(*) AS c, document FROM input GROUP BY (document) HAVING c > 1))"
		c.execute(sql)
		logging.info("Committing changes...")
		db_conn.commit()