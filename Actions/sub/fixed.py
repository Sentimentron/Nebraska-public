#!/usr/bin/env python

"""
    Contains classes used for annotation of subjective
    phrases according to fixed rules.
"""

import re

from collections import defaultdict
from Actions.sub.sub import SubjectivePhraseAnnotator

class FixedSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):
    """
        Annotates subjective phrases according to fixed probability
        tables.
    """
    def insert_entry_term(self, term, prob):
        """Adds a new EntryNode word"""
        self.entries[term] = float(prob)

    def insert_forward_transition(self, term, prob):
        """Adds a ForwardTransition"""
        self.forward[term] = float(prob)

    def insert_backward_transition(self, term, prob):
        """Adds a backward transition"""
        self.backward[term] = float(prob)

    def __init__(self, xml):
        """
            Configurations look like this:
            <FixedSubjectivePhraseAnnotator outputTable="fixed_noprop">
                <EntryNodes>
                    <Word string="bad" prob="1.0" />
                </EntryNodes>
                <ForwardTransitionNodes />
                <BackwardTransitionNodes />
            </FixedSubjectivePhraseAnnotator>
        """
        super(FixedSubjectivePhraseAnnotator, self).__init__(xml)
        # Initialize default items
        self.entries = defaultdict(float)
        self.forward = defaultdict(float)
        self.backward = defaultdict(float)
        # Loop through the children
        for node in xml.iterchildren():
            if node.tag == "EntryNodes":
                for subnode in node.iter():
                    if subnode.tag == "Word":
                        self.insert_entry_term(
                            subnode.get("string"), subnode.get("prob")
                        )
            elif node.tag == "ForwardTransitionNodes":
                for subnode in node.iter():
                    if subnode.tag == "Word":
                        self.insert_forward_transition (
                            subnode.get("string"), subnode.get("prob")
                        )

    def generate_annotation(self, tweet):
        """
            Generates a list of probabilities that each word
            is annotation
        """
        tweet = re.sub("[^a-zA-Z ]", "", tweet)
        tweet = [t for t in tweet.split(' ') if len(t) > 0]
        ret = [0.0 for _ in range(len(tweet))]
        first = False
        for pos, word in enumerate(tweet):
            # Very crude proper noun filtering
            if word[0].lower() != word[0].lower() and not first:
                continue
            first = False
            ret[pos] += self.entries[word]
            if pos < len(tweet)-1:
                ret[pos + 1] += self.forward[word]
            ret.append(self.entries[word])
        return ret
