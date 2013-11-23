#!/usr/bin/env python

"""
	Domain tagger is a special label table, always called the same thing, 
	designed to store which documents are in which domains.

	Documents can belong to more than one domain at the same time.
"""

import logging

from label import Labeller
from lxml import etree
from pprint import pprint
from db import create_sqlite_label_table

class DomainLabeller(Labeller):

	"""

		Some documentation will go here once I reach a computer with the keys in the right place. 

	"""

	def __init__(self, xml):
		super(DomainLabeller, self).__init__("domains")
		self.domain_tree = {}
		for x_node in xml:
			if x_node.tag is etree.Comment:
				continue
			if x_node.tag == "Domain":
				self.recusively_build_domain_tree(x_node)
			else:
				raise ValueError((x_node.tag, "Only Domains are allowed in the top level of the tree!"))

		pprint(self.domain_tree)

	def recusively_build_domain_tree(self, x_node, tree = None):
		
		if tree == None:
			tree = self.domain_tree

		if x_node.tag != "Domain":
			raise ValueError((x_node.tag, "Can only recursively build from Domain tags!"))

		domain = x_node.get("name")

		if domain is None:
			raise ValueError((x_node, "Domains must have a name attribute."))
		if domain not in tree:
			tree[domain] = ({},set([]))
		subdomains, domain_term_set = tree[domain]
		for child in x_node:
			if child.tag is etree.Comment:
				continue 
			if child.tag == "Domain":
				self.recusively_build_domain_tree(child, subdomains)
			elif child.tag == "DomainTerm":
				domain_term_set.add(child.text.lower())
			else:
				raise ValueError((child.tag, "Only Domain and DomainTerm tags can appear here."))


	def _determine_labels(self, tokens, labels, tree, domain):
		"""
			Recursively walk the domain tree, searching for matching 
			domain terms. 

			If a domain term is found, it's added to the labels set.

			Args:
				tokens: set of words in the document 
				labels: set of labels in the document 
				tree: the part of the domain tree we're looking at
				domain: the current domain we're looking at 
		"""
		
		subdomains, domain_term_set = tree
		# Intersect the domain and the document terms sets
		intersecting_terms = tokens & domain_term_set
		if len(intersecting_terms) > 0:
			labels.add(domain)

		# Walk the tree from here 
		for subdomain in subdomains:
			sub_domain_tree = subdomains[subdomain]
			self._determine_labels(tokens, labels, sub_domain_tree, subdomain)

	def determine_labels(self, text, stack=[]):
		# Output setup 
		labels = set([])
		# Basic tokenization
		words = set([w.lower() for w in text.split(' ')])
		# Walk the domain tree
		for domain in self.domain_tree:
			self._determine_labels(words, labels, self.domain_tree[domain], domain)

		return labels 

	def execute(self, path, db_conn):

		# Create the domain label table 
		create_sqlite_label_table("domains", db_conn)

		# Grab a database cursor
		cursor = db_conn.cursor()

		# Retrieve an input size count so we know how long to wait
		sql = "SELECT COUNT(*) FROM input"
		cursor.execute(sql)
		for rowcount, in cursor.fetchall():
			pass 

		# Select everything in the input table 
		sql = "SELECT identifier, document from input";
		cursor.execute(sql)

		current = 0
		for identifier, text in cursor.fetchall():
			current += 1
			labels = self.determine_labels(text) 
			if labels is None:
				continue
			for label in labels:
				self.associate(identifier, label, db_conn)

			if current % 10 == 0:
				print("Determining domain labels (%.2f %% done)\r" % (current * 100.0/rowcount,))

		logging.info("Commiting domain labels...")
		db_conn.commit()

		return True, db_conn