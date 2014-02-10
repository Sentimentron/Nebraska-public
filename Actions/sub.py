#!/usr/bin/env python

"""
    Dealing with subjective phrase annotation/estimation
"""

import math
import re
import logging
from collections import defaultdict, Counter
from results import get_result_bucket
import nltk

from sentiwordnet import SentiWordNetReader

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
        self.metric = xml.get("metric")
        if self.metric == None:
            self.metric = "mse"

        assert self.source is not None
        assert self.predict is not None
        assert self.bucket is not None

    @classmethod
    def pad_annotation(cls, annotation, length):
        if len(annotation) >= length:
            return annotation
        annotation.extend(['0.0' for _ in range(length - len(annotation))])
        return annotation

    @classmethod
    def calc_mse(cls, annotation1, annotation2):

        annotation1 = [i for i in annotation1.split(' ') if len(i) > 0]
        annotation2 = [i for i in annotation2.split(' ') if len(i) > 0]
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        assert len(annotation1) == len(annotation2)
        logging.debug(annotation1)
        logging.debug(annotation2)

        annotation1 = [float(i) for i in annotation1]
        annotation2 = [float(i) for i in annotation2]

        return sum([
            (a1 - a2)*(a1 - a2)
            for a1, a2
            in zip(annotation1, annotation2)
        ])

    @classmethod
    def calc_abs(cls, annotation1, annotation2):
        """
            Reports the annotators ability to correctly identify a word
            which's been highlighted anywhere.
        """
        annotation1 = [float(i) for i in annotation1.split(' ')]
        annotation2 = [float(i) for i in annotation2.split(' ')]
        max_len = max(len(annotation1), len(annotation2))
        annotation1 = cls.pad_annotation(annotation1, max_len)
        annotation2 = cls.pad_annotation(annotation2, max_len)
        result = [(i > 0 and j > 0) or (abs(i-0.05) < 0.05 and abs(j-0.05) < 0.05) for i, j in zip(annotation1, annotation2)]
        return sum([1-int(i) for i in result])

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
            if self.metric == "mse":
                bucket.insert({"prediction": self.predict,
                    "source": self.source,
                    "mse": self.calc_mse(annotation1, annotation2)
                })
            else:
                bucket.insert({"prediction": self.predict,
                    "source": self.source,
                    "abs": self.calc_abs(annotation1, annotation2)
                })

        return True, conn

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

class HumanBasedSubjectivePhraseAnnotator(SubjectivePhraseAnnotator):

    def __init__(self, xml):
        super(HumanBasedSubjectivePhraseAnnotator, self).__init__(
            xml
        )

    def execute(self, path, conn):
        return super(HumanBasedSubjectivePhraseAnnotator, self).execute (
            path, conn
        )

    @classmethod
    def normalize_probability(cls, freq_dist):
        total = sum(freq_dist.values())
        return dict([(i, j / float(total)) for i, j in freq_dist.most_common()])

    @classmethod
    def convert_annotation(cls, ann):
        ann -= 0.001
        ann = max(ann, 0)
        ann = int(math.floor(ann*10))
        if ann >= 4:
            return "4"
        return str(ann)

    @classmethod
    def unconvert_annotation(cls, ann):
        if ann in ["START", "END"]:
            return 0.0
        ann = int(ann)
        ann /= 10.0
        return ann

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

    def group_and_convert_text_anns(self, conn):
        data = self.get_text_anns(conn)
        annotations = {}
        identifier_text = {}
        ret = []
        for identifier, text, ann in data:
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
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            probs = [self.convert_annotation(i) for i in probs]
            ret.append((text, probs))

        return ret

class SubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    """
        Export word-level subjectivity scores to an ARFF file for exploration.
    """

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute.
        """
        super(HumanBasedSubjectivePhraseAnnotator, self).__init__(
            xml
        )
        self.path = xml.get("path")
        assert self.path is not None 

    def group_and_convert_text_anns(self, conn, discretise=True):
        """
            Modified version of super-classes thing: also returns identifiers
        """
        data = self.get_text_anns(conn)
        annotations = {}
        identifier_text = {}
        ret = []
        for identifier, text, ann in data:
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
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            if discretise:
                probs = [self.convert_annotation(i) for i in probs]
            ret.append((text, probs, identifier))

        return ret

    def load_annotations(self, conn):
        """
            Retrieve the majority annotations provided by Turkers
        """
        cursor = conn.cursor()
        sql = "SELECT document_identifier, sentiment FROM subphrases"
        tmp = defaultdict(Counter)
        cursor.execute(sql)
        for identifier, sentiment in cursor.fetchall():
            tmp[identifier].update([sentiment])
            logging.debug((identifier, tmp[identifier]))
        ret = {}
        for identifier in tmp:
            entries = tmp[identifier]
            popular = entries.most_common(2)
            label1, pop1 = popular[0]
            label2, pop2 = popular[1]
            if pop1 == pop2:
                # No consensus, skip
                continue 
            ret[identifier] = label1
        return ret 

    def execute(self, path, conn):
        """
            Outputs an ARFF File containing all the word-level subjectivity 
            scores
        """
        documents = self.group_and_convert_text_anns(conn, discretise=False)
        words = set([])
        output_buf = {}
        labels = self.load_annotations(conn)
        for text, anns, identifier in documents:
            text = text.split(' ')
            first = True
            word_anns = defaultdict(float)
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
                words.add(word)
                word_anns[word] = ann
            output_buf[identifier] = anns

        # Output the ARFF file
        with open(self.path, 'w') as output_file:
            print "@relation subjective" >> output_file
            for word in sorted(words):
                print "@attribute ", word, " numeric" >> output_file 
            print "@attribute overall_annotation {positive, negative, neutral}" >> output_file
            print "" >> output_file
            csv_writer = csv.writer(output_file)
            for identifier in output_buf:
                if identifier not in labels:
                    continue # No consensus for this entry
                csv_writer.writerow([buf[word] for word in sorted(words)] ++ [labels[identifier]])
            csv_writer.close()

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
        logging.info("Building probabilities....")
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

class NTLKSubjectivePhraseMarkovAnnotator(HumanBasedSubjectivePhraseAnnotator):

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
        self.use_mqpa = xml.get("useMQPA")
        if self.use_mqpa == "true":
            self.use_mqpa = True
        else:
            self.use_mqpa = False

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

        if self.use_sw:
            swr = SentiWordNetReader()
            for word, subjectivity in swr.get_subjectivities():
                if '_' in word:
                    continue
                subjectivity = self.convert_annotation(subjectivity*0.5)
                tags.append((subjectivity, word))

        if self.use_mqpa:
            mqpa = MQPASubjectivityReader()
            for word, subjectivity in mqpa.get_subjectivity_pairs('1', '2'):
                tags.append((subjectivity, word))

        print tags
        cfd_tagwords = nltk.ConditionalFreqDist(tags)
        cpd_tagwords = nltk.ConditionalProbDist(cfd_tagwords, nltk.MLEProbDist)
        cfd_tags = nltk.ConditionalFreqDist(nltk.bigrams([tag for (tag, word) in tags]))
        cpd_tags = nltk.ConditionalProbDist(cfd_tags, nltk.MLEProbDist)
        self.distwords = cpd_tagwords
        self.disttags = cpd_tags
        return super(NTLKSubjectivePhraseMarkovAnnotator, self).execute(path, conn)
