#!/usr/bin/env python

"""
    Dealing with subjective phrase annotation/estimation
"""

import math
import re
import logging
from collections import defaultdict
from results import get_result_bucket
import nltk

class SubjectivePhraseAnnotator(object):
    """
        Generates subjective phrase annotations.
    """

    def __init__(self, xml):
        """
            Base constructor
        """
        self.output_table = xml.get("outputTable")
        assert self.output_table is not None
        self.sources = set([])
        self.targets = set([])
        for node in xml.iterchildren():
            if node.tag == "DataFlow":
                for subnode in node.iterchildren():
                    if subnode.tag == "Source":
                        self.sources.add(subnode.text)
                    if subnode.tag == "Target":
                        self.targets.add(subnode.text)



    @classmethod
    def generate_filtered_identifiers(cls, sources, conn):
        """
            Lookup document source labels and get the identifiers
        """
        labcursor = conn.cursor()
        sql = "SELECT label_identifier, label FROM label_names_amt"
        labcursor.execute(sql)
        for identifier, name in labcursor.fetchall():
            if name not in sources:
                continue 
            idcursor = conn.cursor()
            sql = """SELECT document_identifier FROM label_amt WHERE label = ?"""
            idcursor.execute(sql, (identifier,))
            for docid, in idcursor.fetchall():
                yield docid

    def generate_source_identifiers(self, conn):
        """
            Generate identifiers for tweets from files in the <Source /> tags 
        """
        logging.debug(self.sources)
        if len(self.sources) == 0:
            return self.get_all_identifiers(conn) 
        return self.generate_filtered_identifiers(self.sources, conn)

    def generate_target_identifiers(self, conn):
        """
            Generate identifiers for tweets from files in the <Target /> tags 
        """
        if len(self.targets) == 0:
            return self.get_all_identifiers(conn) 
        return self.generate_filtered_identifiers(self.targets, conn)

    @classmethod
    def get_all_identifiers(cls, conn):
        """
            No filtering in effect: just get everything from input
        """
        cursor = conn.cursor()
        sql = "SELECT identifier FROM input"
        cursor.execute(sql)
        for row, in cursor:
            yield row 

    def generate_annotation(self, tweet):
        """Abstract method"""
        raise NotImplementedError()

    @classmethod
    def generate_output_table(cls, name, conn):
        """Generate annotations table"""
        sql = """CREATE TABLE subphrases_%s (
                    identifier INTEGER PRIMARY KEY,
                    document_identifier INTEGER NOT NULL,
                    annotation TEXT NOT NULL,
                    FOREIGN KEY (identifier) REFERENCES input(identifier)
                    ON DELETE CASCADE
            )""" % (name, )
        logging.debug(sql)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()

    @classmethod
    def insert_annotation(cls, name, identifier, annotation, conn):
        """Insert a generated annotation"""
        cursor = conn.cursor()
        annotation = ' '.join([str(i) for i in annotation])
        sql = """INSERT INTO subphrases_%s
            (document_identifier, annotation)
            VALUES (?, ?)""" % (name, )
        cursor.execute(sql, (identifier, annotation))

    def execute(self, _, conn):
        """Create and insert annotations."""
        self.generate_output_table(self.output_table, conn)
        cursor = conn.cursor()
        sql = """SELECT identifier, document FROM input"""
        cursor.execute(sql)
        target_identifiers = set(self.generate_target_identifiers(conn))
        for identifier, document in cursor.fetchall():
            if identifier not in target_identifiers:
                continue
            annotation = self.generate_annotation(document)
            self.insert_annotation(
                self.output_table, identifier, annotation, conn
            )

        conn.commit()
        return True, conn

class EmpiricalSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):
    """
        Probabilistically annotates subjective phases using the
        data given by human annotators
    """
    def __init__(self, xml):
        super(EmpiricalSubjectivePhraseAnnotator, self).__init__(xml)

    def execute(self, _, conn):
        self.generate_output_table(self.output_table, conn)
        cursor = conn.cursor()
        sql = """
            SELECT
                input.identifier, input.document, subphrases.annotation
            FROM input JOIN subphrases
                ON input.identifier = subphrases.document_identifier"""
        cursor.execute(sql)
        annotations = {}
        # Read source annotations
        for identifier, document, annotation in cursor.fetchall():
            if identifier not in annotations:
                annotations[identifier] = []
            annotations[identifier].append(annotation)
        # Compute annotation strings
        for identifier in annotations:
            # Initially zero
            max_len = 0
            for annotation in annotations[identifier]:
                max_len = max(max_len, len(annotation))
            probs = [0.0 for _ in range(max_len)]
            print len(probs)
            for annotation in annotations[identifier]:
                logging.debug((len(annotation), len(probs)))
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            logging.debug(probs)
            # Insert into the database
            self.insert_annotation(self.output_table, identifier, probs, conn)

        conn.commit()
        return True, conn

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

class SubjectiveAnnotationEvaluator(object):

    def __init__(self, xml):
        self.source = xml.get("sourceTable")
        self.predict = xml.get("predictedTable")
        self.bucket = xml.get("bucket")

        assert self.source is not None
        assert self.predict is not None
        assert self.bucket is not None

    @classmethod
    def pad_annotation(cls, annotation, length):
        if len(annotation) >= length:
            return annotation 
        annotation.extend([0.0 for _ in range(length - len(annotation))])
        return annotation

    @classmethod
    def calc_mse(cls, annotation1, annotation2):
        annotation1 = [float(i) for i in annotation1.split(' ')]
        annotation2 = [float(i) for i in annotation2.split(' ')]
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        assert len(annotation1) == len(annotation2)
        return sum([
            (a1 - a2)*(a1 - a2) 
            for a1, a2 
            in zip(annotation1, annotation2)
        ])

    def execute(self, _, conn):
        bucket = get_result_bucket(self.bucket)

        cursor = conn.cursor()
        
        sql = """SELECT subphrases_%s.annotation, subphrases_%s.annotation
            FROM subphrases_%s JOIN subphrases_%s 
            ON subphrases_%s.document_identifier = subphrases_%s.document_identifier"""
        sql = sql % (self.source, self.predict, self.source, 
            self.predict, self.source, self.predict)
        logging.debug(sql)
        cursor.execute(sql)

        for annotation1, annotation2 in cursor.fetchall():
            bucket.insert({"prediction": self.predict, 
                "source": self.source,
                "mse": self.calc_mse(annotation1, annotation2)
            })

        return True, conn 

class NTLKSubjectivePhraseMarkovAnnotator(SubjectivePhraseAnnotator): 

    def __init__(self, xml):
        super(NTLKSubjectivePhraseMarkovAnnotator, self).__init__(
            xml
        )
        self.distwords = None
        self.disttags = None
        self.use_sw = xml.get("useSentiWordNet")
        if self.use_sw == "true":
            self.use_sw = True 
        else:
            self.use_sw = False

    def get_text_anns(self, conn):
        """
            Generate a list of (text, annnotation) pairs
        """
        cursor = conn.cursor()
        ret = []
        sql = """SELECT input.document, subphrases.annotation
        FROM input JOIN subphrases 
        ON input.identifier = subphrases.document_identifier
        WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            for text, anns in cursor.fetchall():
                ret.append((identifier, text, anns))
        return ret 

    @classmethod 
    def convert_annotation(cls, ann):
        ann -= 0.001
        ann = max(ann, 0)
        ann = int(math.floor(ann*10))
        return str(ann)

    @classmethod 
    def unconvert_annotation(cls, ann):
        if ann in ["START", "END"]:
            return 0.0 
        ann = int(ann)
        ann /= 10.0 
        return ann 

    def group_and_convert_text_anns(self, conn):
        data = self.get_text_anns(conn)
        annotations = {}
        identifier_text = {}
        ret = []
        for identifier, text, ann in data:
            logging.debug((identifier, text, ann))
            identifier_text[identifier] = text 
            if identifier not in annotations:
                annotations[identifier] = []
            annotations[identifier].append(ann)

        # Compute annotation strings
        for identifier in annotations:
            # Initially zero
            text = identifier_text[identifier]
            max_len = len(text.split(' '))
            for annotation in annotations[identifier]:
                max_len = max(max_len, len(annotation))
            probs = [0.0 for _ in range(max_len)]
            print len(probs)
            for annotation in annotations[identifier]:
                logging.debug((len(annotation), len(probs)))
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            logging.debug(probs)
            probs = [self.convert_annotation(i) for i in probs]
            logging.debug((text, probs))
            ret.append((text, probs))

        return ret

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

        viterbi = [ ]
        backpointer = [ ]

        distinct_tags = ["START", "END"] + [str(i) for i in range(10)]

        # For each tag, what is the probability it follows START?
        first_tag_seq = {}
        first_back_tag = {}
        for tag in distinct_tags:
            if tag == "START": 
                continue 
            first_tag_seq[tag] = self.disttags["START"].prob(tag)
            first_tag_seq[tag] *= self.distwords[tag].prob(tweet[0])
            first_back_tag[tag] = "START"

        logging.debug(first_tag_seq)
        viterbi.append(first_tag_seq)
        backpointer.append(first_back_tag)

        for word in tweet[1:]:
            this_viterbi = {}
            this_backpointer = {}
            prev_viterbi = viterbi[-1]
            for tag in distinct_tags:
                if tag == "START":
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
        logging.debug((' '.join(tweet), best_tagsequence, prob_tagsequence))
        #return [0.0 for i in best_tagsequence]
        return [self.unconvert_annotation(i) for i in best_tagsequence]

    def execute(self, path, conn):
        documents = self.group_and_convert_text_anns(conn)
        tags = []
        logging.info("Building probabilities....")
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
                word = word.lower()
                word = re.sub('[^a-z]', '', word)
                if len(word) == 0:
                    continue 
                tags.append((ann, word))
            tags.append(("END", "END"))

        cfd_tagwords = nltk.ConditionalFreqDist(tags)
        cpd_tagwords = nltk.ConditionalProbDist(cfd_tagwords, nltk.MLEProbDist)
        cfd_tags = nltk.ConditionalFreqDist(nltk.bigrams([tag for (tag, word) in tags]))
        cpd_tags = nltk.ConditionalProbDist(cfd_tags, nltk.MLEProbDist)
        self.distwords = cpd_tagwords
        self.disttags = cpd_tags
        return super(NTLKSubjectivePhraseMarkovAnnotator, self).execute(path, conn)
