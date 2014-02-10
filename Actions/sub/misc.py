#!/bin/env python

"""
    Contains classes which don't really fit anywhere else in this module
"""

class MQPASubjectivityReader(object):
    def __init__(self, path="Data/subjclueslen1-HLTEMNLP05.tff"):
        self.data = {}
        with open(path, 'rU') as src:
            for line in src:
                line = line.strip()
                atoms = line.split(' ')
                row = {i:j for i,_,j in [a.partition('=') for a in atoms]}
                logging.debug(row)
                self.data[row["word1"]] = row

    def get_subjectivity_pairs(self, strong_strength, weak_strength):
        for word in self.data:
            strength = weak_strength
            if self.data[word]['type'] == 'strongsubj':
                strength = strong_strength
            yield (word, strength)