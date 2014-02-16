#!/usr/bin/env python

"""
    Contains a class for subjective annotation which uses Bayesian
    inference
"""

import re
import logging
import nltk

from collections import Counter

from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator

class NLTKSubjectivePhraseBayesianAnnotator(HumanBasedSubjectivePhraseAnnotator):

    def __init__(self, xml):
        super(NLTKSubjectivePhraseBayesianAnnotator, self).__init__(
            xml
        )
        self.subjworddist = None
        self.subjdist = None
        self.worddist = None

    def word_subj_probability(self, word, sub):
        return self.subjworddist[sub].prob(word)

    def annotate_word(self, word):
        # Looking up which s \in Subjectivity maximizes
        best_annotation = None
        best_score = 0
        for s in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            if s not in self.subjdist:
                continue
            score = self.word_subj_probability(word, s) / self.subjdist[s]
            if score > best_score:
                best_score = score
                best_annotation = s

        return best_annotation

    def generate_annotation(self, tweet):
        first = True
        tweetr = []
        for word in tweet.split(' '):
            if len(word) == 0:
                continue
            if word[0].lower() != word[0] and not first:
                continue
            first = False
            word = word.lower()
            word = re.sub('[^a-z]', '', word)
            if len(word) == 0:
                continue
            tweetr.append(word)
        tweet = tweetr

        if len(tweet) == 0:
            logging.error(("Zero length tweet?", tweet))
            return [0]

        tweet = [self.annotate_word(t) for t in tweet]
        tweet = [self.unconvert_annotation(t) for t in tweet]
        return tweet

    def execute(self, path, conn):
        documents = self.group_and_convert_text_anns(conn)
        tags = []
        for text, anns in documents:
            text = text.split(' ')
            if len(text) != len(anns):
                logging.error(("Wrong annotation length:", anns, text, len(anns), len(text)))
            first = True
            for ann, word in zip(anns, text):
                if len(word) == 0:
                    continue
                if word[0].lower() != word[0] and not first:
                    continue
                first = False
                word = word.lower()
                word = re.sub('[^a-z]', '', word)
                if len(word) == 0:
                    continue
                tags.append((ann, word))

        cfd_tagwords = nltk.ConditionalFreqDist(tags)
        cpd_tagwords = nltk.ConditionalProbDist(cfd_tagwords, nltk.MLEProbDist)
        subj_counter = Counter([tag for tag, word in tags])
        word_counter = Counter([word for tag, word in tags])

        self.subjdist = self.normalize_probability(subj_counter)
        self.worddist = self.normalize_probability(word_counter)
        self.subjworddist = cpd_tagwords
        return super(NLTKSubjectivePhraseBayesianAnnotator, self).execute(path, conn)
