#!/usr/bin/env python

"""
    Code for interacting with CRFSuite
"""

import logging
import math
import re
import subprocess
import tempfile
import types

from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator
from collections import defaultdict

from Actions.sub.word import SubjectiveWordNormaliser

class POSMatchingException(Exception):
    pass

def match_subjectivity(text, postokens, tokens):

    # Convert the pos token identifiers to the
    # actual pos strings
    postokens = [tokens[i] for i in postokens]

    # Split the document in the same way as done
    # for the annotations in the MT form
    text = [i for i in text.split(' ') if len(i.strip()) > 0]

    # Match up the POS tags to the annotations
    # as best we can
    current_pos_tag = 0
    previous_pos_tag = 0
    current_word = 0

    # Step through each word in the tweet
    for text_pos, t in enumerate(text):
        # Set this to something impossible
        pos_word = "ASDFASDFASDF"
        start_pos_range = previous_pos_tag
        output = True
        # Step through the POS tags until we find the first
        # matching word
        while pos_word not in t:
            #logging.debug((pos_word, t, start_pos_range, postokens))
            if start_pos_range >= len(postokens):
                output = False
                break
            next_pos_tag = postokens[start_pos_range]
            pos, _, pos_word = next_pos_tag.partition('/')
            #logging.debug((pos_word, pos_word not in t, t))
            start_pos_range += 1

        # Correct post-increment
        start_pos_range = max(start_pos_range-1, 0)
        # Start searching for the end POS tag from here
        end_pos_range = start_pos_range

        # Step through the tweet until we find the
        # last POS tag that end this text unit
        while pos_word in t:
            if end_pos_range >= len(postokens):
                end_pos_range = len(postokens) + 1
                break
            next_pos_tag = postokens[end_pos_range]
            pos, _, next_pos_word = next_pos_tag.partition('/')
            end_pos_range += 1
            pos_word += next_pos_word

        # Correct post-increment
        end_pos_range = max(end_pos_range-1, 0)

        yield text_pos, start_pos_range, end_pos_range

def match_pos_tags(text, postokens, possibilities, tokens):
    """
        Try to match up the POS tags with the subjectivity annotations
    """

    # Convert the pos token identifiers to the
    # actual pos strings
    postokens = [tokens[i] for i in postokens]

    # Split the document in the same way as done
    # for the annotations in the MT form
    text = [i for i in text.split(' ') if len(i.strip()) > 0]

    # Match up the POS tags to the annotations
    # as best we can
    current_pos_tag = 0
    previous_pos_tag = 0
    current_word = 0

    # Step through each word in the tweet
    for t in text:
        # Set this to something impossible
        pos_word = "ASDFASDFASDF"
        start_pos_range = previous_pos_tag
        output = True
        # Step through the POS tags until we find the first
        # matching word
        while pos_word not in t:
            #logging.debug((pos_word, t, start_pos_range, postokens))
            if start_pos_range >= len(postokens):
                output = False
                break
            next_pos_tag = postokens[start_pos_range]
            pos, _, pos_word = next_pos_tag.partition('/')
            #logging.debug((pos_word, pos_word not in t, t))
            start_pos_range += 1

        # Correct post-increment
        start_pos_range = max(start_pos_range-1, 0)
        # Start searching for the end POS tag from here
        end_pos_range = start_pos_range + 1

        # Step through the tweet until we find the
        # last POS tag that end this text unit
        while pos_word in t:
            if end_pos_range >= len(postokens):
                end_pos_range = len(postokens) + 1
                break
            next_pos_tag = postokens[end_pos_range]
            pos, _, next_pos_word = next_pos_tag.partition('/')
            end_pos_range += 1
            pos_word += next_pos_word
            logging.debug(pos_word)

        # Correct post-increment
        end_pos_range = max(end_pos_range-1, 0)

        # If we didn't find the starting tag, then our
        # POS-tag matching will be hopelessly wrong and
        # we might as well stop.
        if output == False:
            logging.warning(("Couldn't match up the POS tokens: %s (%s)", text, postokens))
            raise POSMatchingException("POS token matching error")

        output = []

        # Otherwise, output each POS-tagged word and the appropriate annotation
        for i in range(start_pos_range, end_pos_range):
            previous_pos_tag = i
            next_pos_tag = postokens[i]
            pos, _, pos_word = next_pos_tag.partition('/')
            # Output the word associated with the POS tag
            # Output the the word associated with this POS tag
            # Output all the possibile subjective annotations for the
            # text unit (approximate word) which contains this POS tag
            if possibilities is not None:
                yield pos_word, pos, possibilities[t]
            else:
                yield pos_word, pos

class CRFSubjectiveExporter(HumanBasedSubjectivePhraseAnnotator):
    """
        Exports subjectivity data to a CRF file for processing.
    """

    def __init__(self, xml, path=None):
        """
            Path attribute is mandatory.
        """
        super(CRFSubjectiveExporter, self).__init__(
            xml
        )
        if path is None:
            self.path = xml.get("path")
        else:
            self.path = path
        assert self.path is not None

        # Warning_set: those where POS coversion failed
        self.warning_set = set([])

        # Maximum and minimum output values
        self.min_annotation = xml.get("min")
        self.max_annotation = xml.get("max")

        if self.min_annotation is None:
            self.min_annotation = 0
        else:
            self.min_annotation = int(self.min_annotation)

        if self.max_annotation is None:
            self.max_annotation = 1
        else:
            self.max_annotation = int(self.max_annotation)

        # Word normalisation options
        self.normaliser = SubjectiveWordNormaliser(xml)

    def group_and_convert_text_anns(self, conn):
        """
            Get subjectivity vectors for each document identifier
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
            for annotation in annotations[identifier]:
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            probs = [self.convert_annotation(i) for i in probs]
            ret.append((identifier, text, probs))

        return ret

    def convert_annotation(self, ann):
        """
            Converts the annotation into a 1 or 0 label,

                1 implies some subjectivity (greater than 10% of people said
                    it was subjective)
                0 implies less than 10% of annotations thought it was subjective
        """
        ann -= 0.001
        ann = max(ann, 0)
        ann = int(math.floor(ann*10))
        if ann > self.max_annotation:
            return str(self.max_annotation)
        elif ann < self.min_annotation:
            return str(self.min_annotation)
        else:
            return '0'

    def execute(self, path, conn):
        """
            Write the CRF file
        """
        annotations = self.group_and_convert_text_anns(conn)
        possibilities = defaultdict(set)
        documents = {}
        identifier_anns = {}
        tokens = self.load_pos_tokens(conn)
        anns = self.load_pos_anns(conn)

        # Determine the subjectivities applied to agiven
        # word anywhere.
        for identifier, text, annotation in annotations:
            documents[identifier] = text
            text = text.split(' ')
            # POS tags are matched up later
            for i, j in zip(text, annotation):
                possibilities[i].add(j)

        # File output section
        with open(self.path, 'w') as output_fp:
            # Each tweet gets output as a section of the CRF
            # file. Sucessive sections get seperated with an
            # extra line space

            for identifier in sorted(documents):
                try:
                    for pos_word, pos_tag, subjectivity in match_pos_tags(documents[identifier], anns[identifier], possibilities, tokens):
                        if self.normaliser.is_stop_word(pos_word):
                            continue
                        # Output the word associated with the POS tag
                        word = self.normaliser.normalise_output_word(pos_word)
                        output_fp.write("%s " % (word,))
                        # Output the the word associated with this POS tag
                        output_fp.write("%s " % (pos_tag, ))
                        # Output all the possibile subjective annotations for the
                        # text unit (approximate word) which contains this POS tag
                        if self.normaliser.is_stopped_pos_tag(pos_tag):
                            output_fp.write("0")
                            continue
                        for s in subjectivity:
                            output_fp.write(s)
                            output_fp.write(" ")
                        # End this entry
                        output_fp.write("\n")

                    # Output the document-separating line space
                    output_fp.write("\n")
                except POSMatchingException:
                    self.warning_set.add(identifier)

        return True, conn

class ProduceCRFSTagList(object):
    """
        This class takes care of the mechanics of outputting
        CRF files, training CRFSuite to produce a model and
        then tagging.
    """

    def __init__(self, xml, test_path = None, train_path = None, results_path = None):
        """
            Required:
                test_path attribute
                train_path attribute
            Optional:
                results_path
                    If unspecified, "crf_results.txt" gets created in current directory
        """
        if xml != None:
            self.test_path = xml.get("test_path")
            self.train_path = xml.get("train_path")
            self.results_path = xml.get("results_path")
        else:
            self.test_path = test_path
            self.train_path = train_path
            self.results_path = results_path

        assert self.test_path is not None
        assert self.train_path is not None

        if self.results_path is None:
            self.results_path = "crf_results.txt"

    def execute(self, path, conn):
        with tempfile.NamedTemporaryFile() as model_fp:
            with tempfile.NamedTemporaryFile() as train_dest_fp:
                # Chunk the training data
                with open(self.train_path, 'r') as train_fp:
                    subprocess.check_call(["python", "Actions/chunking.py"], stdin=train_fp, stdout=train_dest_fp)
                # Chunk the testing data
                with tempfile.NamedTemporaryFile() as test_dest_fp:
                    with open(self.test_path, 'r') as test_fp:
                        subprocess.check_call(["python", "Actions/chunking.py"], stdin=test_fp, stdout=test_dest_fp)

                    # Train the model
                    args = "crfsuite learn -p max_linesearch=40 -m %s %s"
                    s = subprocess.Popen(args % (model_fp.name, train_dest_fp.name), shell=True, stdout=subprocess.PIPE)
                    while True:
                        line = s.stdout.readline()
                        if not line:
                            break
                        logging.info(line)

                    # Test the model
                    args = "crfsuite tag -qt -m %s %s"
                    s = subprocess.Popen (args % (model_fp.name, test_dest_fp.name), shell=True, stdout=subprocess.PIPE)
                    while True:
                        line = s.stdout.readline()
                        if not line:
                            break
                        logging.info(line)

                    with open(self.results_path, 'w') as out_fp:
                        # Tag the output
                        args = "crfsuite tag -m %s %s"
                        subprocess.check_call(args % (model_fp.name, test_dest_fp.name), shell=True, stdout=out_fp)

                    logging.debug("%s %s %s", train_dest_fp.name, test_dest_fp.name, model_fp.name)

        return True, conn

class CRFSubjectiveAnnotator(HumanBasedSubjectivePhraseAnnotator):

    """
        Annotates subjective phrases using external CRF library
    """

    def __init__(self, xml):
        """
            outputTable: optional parameter
        """
        self.output_table = xml.get("outputTable")
        self.test_fp = tempfile.NamedTemporaryFile()
        self.train_fp = tempfile.NamedTemporaryFile()
        self.results_fp = tempfile.NamedTemporaryFile()
        logging.debug("CRFSubjectiveAnnotator: %s %s %s",
            self.test_fp.name, self.train_fp.name, self.results_fp.name
            )
        # Create exporter scripts
        self.test_exporter = CRFSubjectiveExporter(xml, self.test_fp.name)
        self.train_exporter = CRFSubjectiveExporter(xml, self.train_fp.name)
        self.worker = ProduceCRFSTagList(
            None, self.test_fp.name, self.train_fp.name, self.results_fp.name
        )

    def stub_target_table(self, table):
        pass

    def parse_output(self):
        self.results_fp.seek(0)
        buf = []
        for line in self.results_fp:
            line = line.strip()
            if len(line) == 0:
                yield buf
                buf = []
                continue
            buf.append(int(line))

    def execute(self, path, conn):

        # Plug exporter methods with our own
        self.train_exporter.generate_source_identifiers = types.MethodType(lambda s, y: self.generate_source_identifiers(conn), self.train_exporter)
        self.test_exporter.generate_source_identifiers = types.MethodType(lambda s, y: self.generate_target_identifiers(conn), self.test_exporter)

        # Export the training and test files
        result, conn = self.train_exporter.execute(path, conn)
        assert result
        result, conn = self.test_exporter.execute(path, conn)
        assert result

        # Ask the worker to train and tag things
        result, conn = self.worker.execute(path, conn)
        assert result

        documents =  self.get_text(conn, self.generate_target_identifiers(conn))
        tokens = self.load_pos_tokens(conn)
        postags = self.load_pos_anns(conn)

        subjectivity_vec = self.parse_output()
        #logging.debug([i for i in subjectivity_vec])

        identifiers = set(documents)
        identifiers -= self.test_exporter.warning_set

        for identifier, subjectivity in zip(sorted(identifiers), self.parse_output()):
            text = documents[identifier]
            tags = postags[identifier]

            text_subjectivity = {}
            for i, j, k in match_subjectivity(text, tags, tokens):
                textsubj = subjectivity[j:k+1]
                if len(textsubj) == 0:
                    logging.error((i, j, k, text))
                textsubj = sum(textsubj) / max(len(textsubj), 1)
                assert i not in text_subjectivity
                text_subjectivity[i] = textsubj

            self.insert_annotation(
                self.output_table, identifier, [self.unconvert_annotation(text_subjectivity[i]) for i in sorted(text_subjectivity)], conn
            )
        return True, conn

