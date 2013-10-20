#!/usr/bin/env python

def fetch_metadata(key, db_conn):
	cur = db_conn.cursor()
	sql = "SELECT value FROM metadata WHERE key = ?"
	cur.execute(sql, (key,))
	for val, in cur.fetchall():
		return val 
	return None

def push_metadata(key, val, db_conn):
	cur = db_conn.cursor()
	if fetch_metadata(key, db_conn) is None:
		sql = "INSERT INTO metadata (key, value) VALUES (?, ?)"
		cur.execute(sql, (key, val))
	else:
		sql = "UPDATE metadata SET value = ? WHERE key = ?"
		cur.execute(sql, (val, key))
	db_conn.commit()