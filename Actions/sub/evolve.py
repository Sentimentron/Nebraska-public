#!/usr/bin/env python

"""
    Can we "evolve" subjectivity?
"""

import nltk
from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator
from collections import defaultdict, Counter
import random
import itertools
import logging
import copy
import re
from nltk.stem.porter import PorterStemmer

class SubjectiveEvolution(HumanBasedSubjectivePhraseAnnotator):
    """
        This class aims to find out.
    """

    def __init__(self, xml):
        super(SubjectiveEvolution, self).__init__(
            xml
        )

        self.genome = defaultdict(float)
        self.count = defaultdict(int)
        self.store = []

    def calc_mse(self, vector1, vector2):
        """Calculate the mean squared error between vector1 and 2"""
        return sum([
            (i - j) * (i - j)
            for i, j in itertools.izip_longest(vector1, vector2, fillvalue=0.0)
        ])

    def generate_genome(self, mutation_set):
        # Copy the genome

        # Select two genomes from the store
        genome1,_ = random.choice(self.store)
        genome2,_ = random.choice(self.store)

        # Copy the genome
        genome = copy.deepcopy(genome1)
        for i in genome:
            if random.random() < 0.5:
                genome[i] = genome2[i]

        # Mutate the scores
        for i in genome:
            r = random.random()
            if i not in mutation_set:
                continue
            if r > 0.05:
                continue
            a = random.random() * 0.4
            a -= 0.2
            genome[i] += a
        return genome

    def score_bigram(self, bigram, genome):
        i1, i2 = bigram
        total_score = genome[bigram] * self.count[bigram]
        total_score += genome[i1] * self.count[i1]
        total_score += genome[i2] * self.count[i2]
        total_count = self.count[bigram]
        total_count += self.count[i1]
        total_count += self.count[i2]
        try:
            return total_score / total_count
        except ZeroDivisionError:
            logging.debug((i1, i2, self.count[i1], self.count[i2], self.count[(i1, i2)]))

    def push_genome_score(self, new_genome, new_score):
        min_score = 99999999
        max_score = 0
        avg = []
        # Condition 1: we haven't got enough genomes in the library yet
        if len(self.store) < 10:
            self.store.append((new_genome, new_score))
            logging.info("ACCEPTED INITIAL GENOME WITH SCORE %.2f", new_score)
            return False

        # Find maximum, minimum and average scores
        for index, (_, score) in enumerate(self.store):
            min_score = min(min_score, score)
            max_score = max(max_score, score)
            avg.append(score)
        avg = sum(avg) / len(self.store)

        # Reject the genome if it's not up to code
        if new_score > avg:
            logging.info(
                "REJECTED %.2f (Max: %.2f / Average: %.2f)",
                new_score, max_score, avg
            )
            return abs(max_score - min_score) < 0.005

        logging.info(
            "ACCEPTED %.2f (Max: %.2f / Average: %.2f)",
            new_score, max_score, avg
        )
        # Otherwise, insert the genome
        for index, (genome, score) in enumerate(self.store):
            if score != max_score:
                continue
            self.store[index] = (new_genome, new_score)

        # Find the new minimum score
        min_score = 999999
        max_score = 0
        for index, (genome, score) in enumerate(self.store):
            min_score = min(min_score, score)
            max_score = max(max_score, score)

        return abs(max_score - min_score) < 0.005

    def evaluate_genome_on_sentence(self, genome, bigrams, anns):
        score_vector = []
        for bigram in bigrams:
            score_vector.append(self.score_bigram(bigram, genome))
        return self.calc_mse(score_vector, anns)

    def evaluate_genome(self, genome, training_set):
        total_score = 0
        limit = 0
        for bigrams, anns in training_set:
            total_score += self.evaluate_genome_on_sentence(genome, bigrams, anns)
        return total_score

    def train(self, training_set):
        converged = False
        # Generate mutation set
        mutation_set = set(itertools.chain.from_iterable([i for i,j in training_set]))
        mutation_set2 = copy.copy(mutation_set)
        for bigram in mutation_set2:
            for word in bigram:
                mutation_set.add(word)
        while not converged:
            genome = self.generate_genome(mutation_set)
            score = self.evaluate_genome(genome, training_set)
            converged = self.push_genome_score(genome, score)

    def get_worst_squared_error(self, genome, training_set, subtraining_set):
        worst_score = 0
        worst_sentence = None
        for bigrams, anns in training_set:
            score = self.evaluate_genome_on_sentence(genome, bigrams, anns)
            if score > worst_score and worst_sentence not in subtraining_set:
                worst_score = score
                worst_sentence = (bigrams, anns)
        return worst_sentence

    def execute(self, path, conn):

        # Get the source and target annotations
        source_ids = self.generate_source_identifiers(conn)
        target_ids = self.generate_target_identifiers(conn)

        # Get the list of subjective annotations
        documents = self.group_and_convert_text_anns(conn, True)

        ps = PorterStemmer()

        # Build the initial genome
        for text, anns, identifier in documents:
            text = text.split(' ')
            anns = [int(i) * 0.1 for i in anns]
            for (a1, a2), (i, j) in zip(nltk.bigrams(anns), nltk.bigrams(text)):
                if i in nltk.corpus.stopwords.words('english'):
                    i = "STOPPED_WORD"
                if j in nltk.corpus.stopwords.words('english'):
                    j = "STOPPED_WORD"
                if "@" in i:
                    i = "AT"
                if "@" in j:
                    j = "AT"
                if "#" not in i:
                    i = ps.stem(i)
                if "#" not in j:
                    j = ps.stem(j)
                i = i.lower()
                j = j.lower()
                i = re.sub('[^a-z0-9#]', '', i)
                j = re.sub('[^a-z0-9#]', '', j)
                if len(i) == 0:
                    i = "FILTERED_WORD"
                if len(j) == 0:
                    j = "FILTERED_WORD"
                self.genome[(i, j)] += 0.5 * (a1 + a2)
                self.count[(i, j)] += 1
                self.genome[i] += a1
                self.count[i] += 1
                self.genome[j] += a2
                self.count[j] += 1
        for i in self.genome:
            self.genome[i] /= self.count[i]

        training_set = []

        for text, anns, identifier in documents:
            anns = [int(i) * 0.1 for i in anns]
            text = text.split(' ')
            if identifier in source_ids:
                buf_text = []
                buf_anns = []
                for (a1, a2), (i, j) in zip(zip(anns[:-1], anns[1:]), nltk.bigrams(text)):
                    if i in nltk.corpus.stopwords.words('english'):
                        i = "STOPPED_WORD"
                    if j in nltk.corpus.stopwords.words('english'):
                        j = "STOPPED_WORD"
                    if "@" in i:
                        i = "AT"
                    if "@" in j:
                        j = "AT"
                    if "#" not in i:
                        i = ps.stem(i)
                    if "#" not in j:
                        j = ps.stem(j)
                    i = i.lower()
                    j = j.lower()
                    i = re.sub('[^a-z0-9#]', '', i)
                    j = re.sub('[^a-z0-9#]', '', j)
                    if len(i) == 0:
                        i = "FILTERED_WORD"
                    if len(j) == 0:
                        j = "FILTERED_WORD"
                    if ";" in i:
                        logging.error(i)
                        assert False
                    buf_text.append((i, j))
                    buf_anns.append(0.5 * (a1 + a2))
                training_set.append((buf_text, buf_anns))

        subtraining_set = []
        while len(subtraining_set) < len(training_set):
            self.store = []
            worst_sentence = self.get_worst_squared_error(self.genome, training_set, subtraining_set)
            logging.debug(worst_sentence)
            subtraining_set.append(worst_sentence)
            score = self.evaluate_genome(self.genome, subtraining_set)
            self.push_genome_score(self.genome, score)
            self.train(subtraining_set)
            self.genome, _ = self.store[0]

        return True, conn
