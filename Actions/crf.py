#!/usr/bin/env python

import tempfile
import os
import subprocess
import logging

from nltk.corpus import wordnet as wn

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

class CRFNativeExporter(object):

    def __init__(self, xml):

        self.cross_validate = xml.get("cross_validate")
        if self.cross_validate is not None:
            self.cross_validate = int(self.cross_validate)

        self.prefix = xml.get("prefix")
        if self.prefix is None:
            hnd, self.prefix = tempfile.mkstemp(suffix=".crf", prefix=os.getcwd() + "/")

        self.subphrase_src = xml.get("subphrase_src")
        if self.subphrase_src is None:
            self.subphrase_src = "subphrases"

        self.tags_src = xml.get("tags_src")
        if self.tags_src is None:
            self.tags_src = "gimpel"
        self.tags_src = "pos_off_%s" % (self.tags_src,)

    def execute(self, path, conn):

        cursor = conn.cursor()
        sql = """SELECT document_identifier, annotation from %s""" % (self.subphrase_src, )
        cursor.execute(sql)
        annotation_buf = list(cursor.fetchall())

        output_file = open(self.prefix, 'w')

        communicator = ProduceCRFSTagList(None, "test_path", self.prefix, "crf_result")

        for identifier, annotation in annotation_buf:
            # Retrieve source annotation text
            sql = """SELECT pos_norm_gimpel.document FROM pos_norm_gimpel
                        JOIN input ON pos_norm_gimpel.document_identifier = input.identifier
                        WHERE input.document = pos_norm_gimpel.document
                        AND input.identifier = ?"""
            cursor.execute(sql, (identifier,))
            text = None
            for text, in cursor.fetchall():
                pass
            if text is None:
                continue
            text = text.split(' ')

            annotations_map = []
            text_map = []
            counter = 0
            for a,t in zip(annotation, text):
                text_map.append((counter, t))
                annotations_map.append((counter, a))
                counter += len(t) + 1 # For the space

            # Retrieve the output tokens
            sql = """SELECT start,word,tag,synset FROM %s WHERE document_identifier = ? ORDER BY start""" % (self.tags_src,)
            cursor.execute(sql, (identifier,))
            for start, word, tag, synset in cursor.fetchall():
                # Step through the annotation dict until we get to the start
                s, a = sorted(annotations_map, key=lambda x: abs(x[0]-start))[0]

                if synset is not None:
                    synset = wn.synset(synset)
                    human_read = synset.name
                    root, pos, sense = human_read.split('.')
                    output = "%s.%s\t%s" % (word, sense, tag)
                else:
                    output = "%s\t%s" % (word, tag)

                output_file.write("%s\t%s\n", output, a)

            output_file.write("\n")

        output_file.close()

        for identifier, annotation in annotation_buf:

            output_file = open("test_fp", "r")
            #
            # TODO: REFACTOR
            # Retrieve source annotation text
            sql = """SELECT document FROM pos_norm_gimpel
                        JOIN input ON pos_norm_gimpel.document_identifier = input.identifier
                        WHERE input.document = pos_norm_gimpel.document
                        AND input.identifier = ?"""
            cursor.execute(sql, (identifier,))
            text = None
            for text, in cursor.fetchall():
                pass
            if text is None:
                continue
            text = text.split(' ')

            annotations_map = []
            text_map = []
            counter = 0
            for a,t in zip(annotation, text):
                text_map.append((counter, t))
                annotations_map.append((counter, a))
                counter += len(t) + 1 # For the space

            # Retrieve the output tokens
            sql = """SELECT start,word,tag,synset FROM %s WHERE document_identifier = ? ORDER BY start""" % (self.tags_src,)
            cursor.execute(sql)
            for start, word, tag, synset in cursor.fetchall():
                # Step through the annotation dict until we get to the start
                s, a = sorted(annotations_map, key=lambda x: abs(x[0]-start))

                if synset is None:
                    synset = wn.synset(synset)
                    human_read = synset.name
                    root, pos, sense = human_read.split('.')
                    output = "%s.%s\t%s" % (word, sense, tag)
                else:
                    output = "%s\t%s" % (word, tag)

                output_file.write("%s\t%s\n", output, a)

            output_file.write("\n")

            output_file.close()

            communicator.execute(path,conn)

            with open("crf_result", "r") as fp:
                buf = []
                for line in fp:
                    buf.append(line.strip())
                print annotation
                print ''.join(buf)

        return True, conn

