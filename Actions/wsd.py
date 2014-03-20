#!/usr/bin/env python
"""
    Contains functions for standard word normalisation and stemming
"""

import pdb
import logging

from itertools import chain
from nltk.corpus import wordnet as wn
from nltk.stem.porter import PorterStemmer

class WordSenseDisambiguate(object):

    """
        Word-sense disambiguation using Lesk

        Stores in pos_off_ tables
    """

    def __init__(self, xml):
        self.ps = PorterStemmer()
        self.table = "pos_off_%s" % (xml.get("table"), )
        self.src_table = "pos_norm_%s" % (xml.get("table"), )
        assert xml.get("table") is not None

    def lesk(self, context_sentence, ambiguous_word, pos):
        """
            Attempts to determine the word sense
            Returns None if one could not be determined
        """
        lesk_sense = None
        max_overlaps = 0

        for ss in wn.synsets(ambiguous_word, pos=pos):
            lesk_dictionary = ss.definition.split()
            lesk_dictionary += ss.lemma_names
            lesk_dictionary += list(chain(*[
                i.lemma_names for i in ss.hypernyms()
                    + ss.hyponyms()]))
            lesk_dictionary = [self.ps.stem(i) for i in lesk_dictionary]
            context_sentence = [self.ps.stem(i) for i in context_sentence]
            overlaps = set(lesk_dictionary).intersection(context_sentence)

            if len(overlaps) > max_overlaps:
                lesk_sense = ss
                max_overlaps = len(overlaps)

        return lesk_sense

    @classmethod
    def translate_pos_tag(cls, tag):
        """
            Translate the POS tag produced by Gimpel into
            a WordNet equivalent. Return None if there's no equivalent
        """
        if tag in ["N", "S", "L"]:
            return wn.NOUN # May include nominal, requires stemming
        if tag in ["V"]:
            return wn.VERB
        if tag in ["A"]:
            return wn.ADJ
        if tag in ["R"]:
            return wn.ADV

        return None

    def execute(self, path, conn):
        """
            Update output table to include synsets where applicable
        """
        logging.basicConfig(level=logging.DEBUG)
        cur = conn.cursor()
        subcur = conn.cursor()
        sql = """SELECT identifier,
                    document_identifier,
                    word,
                    tag
                FROM %s""" % (self.table,)
        logging.debug(sql)
        cur.execute(sql)
        for identifier, doc_identifier, word, tag in cur.fetchall():
            logging.debug((identifier, doc_identifier, word, tag))
            wn_tag = self.translate_pos_tag(tag)
            if wn_tag == None:
                continue
            logging.debug(wn_tag)
            synsets = wn.synsets(word, pos=wn_tag)
            logging.debug(synsets)
            synset = None
            if len(synsets) == 1:
                synset = synsets[0]
            else:
                sql = """SELECT document
                            FROM %s
                            WHERE document_identifier = %d
                      """ % (self.src_table, doc_identifier)
                subcur.execute(sql)
                for text, in subcur.fetchall():
                    synset = self.lesk(text, word, wn_tag)
            logging.debug(synset)
            if synset is None:
                continue
            sql = """UPDATE %s SET synset = ? WHERE identifier = ?""" % (self.table,)
            subcur.execute(sql, (synset.name, identifier))

        conn.commit()
        return conn, True
