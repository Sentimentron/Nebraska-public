#!/usr/bin/env python

"""
    Contains a class for subjective annotation which uses Markov
    chains
"""

import re
import nltk
import logging
from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator
from Actions.sub.word import SubjectiveWordNormaliser


class NTLKSubjectivePhraseMarkovAnnotator(HumanBasedSubjectivePhraseAnnotator):

    def __init__(self, xml):
        super(NTLKSubjectivePhraseMarkovAnnotator, self).__init__(
            xml
        )
        self.distwords = None
        self.disttags = None
        self.normaliser = SubjectiveWordNormaliser(xml)

    def generate_annotation(self, tweet):
        """
            Generates a list of probabilities that each word's
            annotation.

            Adapted from:
            http://www.katrinerk.com/courses/python-worksheets/hidden-markov-models-for-pos-tagging-in-python
        """
        first = True
        tweetr = []
        for word in tweet.split(' '):
            word = self.normaliser.normalise_output_word(word)
            if len(word) == 0:
                continue
            tweetr.append(word)
        tweet = tweetr

        if len(tweet) == 0:
            logging.error(("Zero length tweet?", tweet))
            return [0]

        viterbi = [ ]
        backpointer = [ ]

        distinct_tags = ["START", "END"] + [str(i) for i in range(10)]

        # For each tag, what is the probability it follows START?
        first_tag_seq = {}
        first_back_tag = {}
        for tag in distinct_tags:
            if tag == "START":
                continue
            if tag == "END":
                continue
            first_tag_seq[tag] = self.disttags["START"].prob(tag)
            first_tag_seq[tag] *= self.distwords[tag].prob(tweet[0])
            first_back_tag[tag] = "START"

        viterbi.append(first_tag_seq)
        backpointer.append(first_back_tag)

        for word in tweet[1:]:
            this_viterbi = {}
            this_backpointer = {}
            prev_viterbi = viterbi[-1]
            for tag in distinct_tags:
                if tag == "START":
                    continue
                if tag == "END":
                    continue
                best_prev = max(prev_viterbi.keys(),
                    key = lambda x: prev_viterbi[x] * self.disttags[x].prob(tag)
                    * self.distwords[x].prob(word))
                this_viterbi[tag] = prev_viterbi[best_prev] * self.disttags[best_prev].prob(tag) * self.distwords[tag].prob(word)
                this_backpointer[tag] = best_prev

            viterbi.append(this_viterbi)
            backpointer.append(this_backpointer)

        #logging.debug(viterbi)
        prev_viterbi = viterbi[-1]
        best_previous = max(prev_viterbi.keys(), key=lambda x: prev_viterbi[x] * self.disttags[x].prob("END"))
        prob_tagsequence = prev_viterbi[best_previous] * self.disttags[best_previous].prob("END")
        best_tagsequence = ["END", best_previous]
        backpointer.reverse()

        current_best_tag = best_previous
        for bp in backpointer:
            best_tagsequence.append(bp[current_best_tag])
            current_best_tag = bp[current_best_tag]

        best_tagsequence.reverse()
        #return [0.0 for i in best_tagsequence]
        return [self.unconvert_annotation(i) for i in best_tagsequence]

    def execute(self, path, conn):
        documents = self.group_and_convert_text_anns(conn)
        tags = []
        for text, anns in documents:
            text = text.split(' ')
            if len(text) != len(anns):
                logging.error(("Wrong annotation length:", anns, text, len(anns), len(text)))
            tags.append(("START", "START"))
            first = True
            for ann, word in zip(anns, text):
                if len(word) == 0:
                    continue
                if word[0].lower() != word[0] and not first:
                    continue
                first = False
                word = self.normaliser.normalise_output_word(word)
                tags.append((ann, word))
            tags.append(("END", "END"))

        cfd_tagwords = nltk.ConditionalFreqDist(tags)
        cpd_tagwords = nltk.ConditionalProbDist(cfd_tagwords, nltk.MLEProbDist)
        cfd_tags = nltk.ConditionalFreqDist(nltk.bigrams([tag for (tag, word) in tags]))
        cpd_tags = nltk.ConditionalProbDist(cfd_tags, nltk.MLEProbDist)
        self.distwords = cpd_tagwords
        self.disttags = cpd_tags
        return super(NTLKSubjectivePhraseMarkovAnnotator, self).execute(path, conn)
