#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Contains a SentiWordNet reader
"""

import logging
from templabeller import LiteralLabeller

class SentiWordNetStrengthLabeller(LiteralLabeller):

    def __init__(self, xml):
        super(SentiWordNetStrengthLabeller, self).__init__(xml)
        self.threshold = float(xml.get("threshold"))
        self.swr = SentiWordNetReader()

    def label(self, document):
        for word in document.split(' '):
            word = word.lower().strip()
            if len(word) == 0:
                continue
            score = self.swr.get_max_tuple(word)
            if score is None:
                continue
            pos, neg = score
            if pos >= self.threshold or neg >= self.threshold:
                return 1
        return 0


class SentiWordNetReader(object):

    """
        Stores scores and other info read from SentiWordNet

        path: path to SW database
        scores: id -> (pos, neg score) mapping
        synset_id_map: (synset -> id) mapping
        synset_pos_map:
        word_synset_map:
    """

    def __init__(self, path="Data/SentiWordNet_3.0.0_20120510.txt"):
        """
            Reads a SentiWordNet file
        """
        self.path = path
        self.scores = {}
        self.synset_id_map = {}
        self.synset_pos_map = {}
        self.word_synset_map = {}

        with open(self.path, 'r') as sentif:
            for line in sentif:
                if line[0] == '#': # Comment line
                    continue
                # Split the columns
                columns = line.split('\t')
                #logging.debug(columns)
                pos, id_, pos_score, neg_score, synsets, _ = columns
                if len(pos.strip()) == 0:
                    break
                # Convert the scores
                pos_score, neg_score = float(pos_score), float(neg_score)
                # Convert the identifier
                id_ = int(id_)
                # Store the score
                self.scores[id_] = (pos_score, neg_score)
                # Split the synsets
                synsets = synsets.split(' ')
                for synset in synsets:
                    self.synset_id_map[synset] = id_
                    self.synset_pos_map[synset] = pos
                    word, _, _ = synset.partition('#')
                    if word not in self.word_synset_map:
                        self.word_synset_map[word] = set([])
                    self.word_synset_map[word].add(synset)

    def get_max_tuple(self, word):
        if word not in self.word_synset_map:
            return None
        synsets = self.word_synset_map[word]
        identifiers = set([])
        for synset in synsets:
            identifier = self.synset_id_map[synset]
            identifiers.add(identifier)
        biggest_pos, biggest_neg = 0, 0
        for identifier in identifiers:
            pos, neg = self.scores[identifier]
            biggest_pos = max(biggest_pos, pos)
            biggest_neg = max(biggest_neg, neg)
        return biggest_pos, biggest_neg


    def get_subjectivity(self, word):
        """
            Return a float between 0 and 1 describing the subjectivity
            of a word.
        """
        if word not in self.word_synset_map:
            return None
        synsets = self.word_synset_map[word]
        identifiers = set([])
        for synset in synsets:
            identifier = self.synset_id_map[synset]
            identifiers.add(identifier)
        total, count = 0.0, 0
        for identifier in identifiers:
            pos, neg = self.scores[identifier]
            total += 1 - (pos + neg)
            count += 1

        return total / max(count, 1)