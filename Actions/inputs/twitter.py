#!/usr/bin/env python

import os 
import logging
import sqlite3
import tempfile
import subprocess

class TwitterCompressedDBInputSource(object):

	def __assert_path_exists(self):
		if not os.path.exists(self.path):
			raise IOError("_TwitterInputSource: file '%s' does not exist!", (self.path,))

	def __init__(self, path):
		self.path = path 
		self.__assert_path_exists()

	def decompress(self):
		hnd, tmp = tempfile.mkstemp(suffix='.sqlite') 
		try:
			logging.info("Decompressing '%s' to '%s'...", self.path, tmp)
			# Open the decompression output
			tmp_fp = open(tmp, 'w')
			# Open the decompression input
			src_fp = open(self.path, 'r')
			# Decompress the file
			p = subprocess.Popen(["xz", "-d"], stdin=src_fp, stdout=tmp_fp)
			p.communicate()
			# Close the input
			tmp_fp.close()
			src_fp.close()
			return tmp
		except Exception as ex:
			os.remove(tmp)
			raise ex  

	def run_import(self):
		tmp = self.decompress()
		con = sqlite3.connect(tmp)
		try:
			cur = con.cursor()
			# Retrieve some metadata so we know how to handle the file 
			metadata = {}
			sql = "SELECT * FROM metadata"
			cur.execute(sql)
			for key, value in cur.fetchall():
				metadata[key] = value 
			# Check that we recognise the input 
			if metadata["data_format"] != "TWEET_TEXT":
				logging.warn("data format: unrecognised value '%s'. Skipping import...", metadata["data_format"])
				return 
			# Select document text from the input table 
			sql = "SELECT response FROM stream"
			cur.execute(sql)
			for text, in cur.fetchall():
				yield text 
		finally:
			con.close()
			# os.remove(tmp)

class TwitterInputSource(object):

	def __assert_directory_exists(self):
		if not os.path.exists(self.directory):
			raise IOError("TwitterInputSource: directory '%s' does not exist!", (self.directory, ))

	def __init__(self, xml):
		self.xml = xml
		self.directory = xml.get("dir")
		self.__assert_directory_exists()

	def get_import_files(self):
		ret = set([])
		# Get suitable files in the directory
		for root, _, files in os.walk(self.directory):
			for filename in files:
				extension = os.path.splitext(filename)[1][1:].strip()
				if extension != "xz":
					continue 
				ret.add(os.path.join(root, filename))

		return ret 

	def run_import(self, files):
		input_sources = []
		for filename in files:
			input_sources.append(TwitterCompressedDBInputSource(filename))

		for src in input_sources:
			for text in src.run_import():
				yield text, "Undefined", "Undefined"