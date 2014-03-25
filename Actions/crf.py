#!/usr/bin/env python

import os
import sys
import subprocess
import logging
import crfsuite
import tempfile
import traceback

from time import gmtime, strftime
from collections import defaultdict, Counter

import pdb

from nltk.corpus import wordnet as wn
import unicodedata

"""
    My vision:

    <CRFSubjectivityTagger mode="evaluate" folds="5" resultsPath="crf" maxFeatures="unlimited" />
    <CRFSubjectivityTagger mode="train" modelFile="model" />
    <CRFSubjectivityTagger mode="tag" modelFile="model" subphrase_dest />

"""


class CRFStubTrainer(crfsuite.Trainer):

    def message(self, s):
        sys.stdout.write(s)

class CRFSubjectivityTagger(object):

    def __init__(self, xml):

        self.subphrase_src = xml.get("subphrase_src")
        if self.subphrase_src is None:
            self.subphrase_src = "subphrases"

        self.mode = xml.get("mode")
        if self.mode == "evaluate":
            self.log_path = xml.get("resultsPath")
            assert self.log_path is not None
        self.model_path = xml.get("modelPath")
        assert self.model_path is not None
        if self.mode == "tag":
            self.output_table = xml.get("subphraseDest")
            assert self.output_table is not None
        if self.mode not in ["evaluate","train","tag"]:
            raise ValueError((self.mode, "Invalid operation"))

    @classmethod
    def convert_to_crfsuite_instances(cls, instances, yield_yseq=True):
        for instance in instances:
            xseq = crfsuite.ItemSequence()
            if yield_yseq:
                yseq = crfsuite.StringList()
            old_word = "START"
            old_pos = "START"
            for identifier, word, pos, subj in instance:
                word = unicodedata.normalize('NFKD',word).encode('ascii','ignore')
                pos = unicodedata.normalize('NFKD',pos).encode('ascii','ignore')
                if subj is not None:
                    subj = unicodedata.normalize('NFKD',subj).encode('ascii','ignore')
                item = crfsuite.Item()
                try:
                    item.append(crfsuite.Attribute(word))
                    item.append(crfsuite.Attribute(pos))
                except:
                    type, value, tb = sys.exc_info()
                    traceback.print_exc()
                    pdb.post_mortem(tb)

                old_word, old_pos = word, pos
                xseq.append(item)
                if yield_yseq:
                    weight = 1
                    if subj == 's':
                        weight = 10
                    yseq.append(subj)

            if yield_yseq:
                yield identifier, xseq, yseq
            else:
                yield identifier, xseq

    @classmethod
    def train_and_output_model(cls, instances, model_path):
        trainer = CRFStubTrainer()

        for _, xseq, yseq in cls.convert_to_crfsuite_instances(instances):
            trainer.append(xseq, yseq, 0)

        trainer.select("arow", "crf1d")
        trainer.set("variance", "0.1")
        trainer.set("max_iterations", "300");
        trainer.set("gamma", "0.5")

        trainer.train(model_path,-1)

    @classmethod
    def tag_instances_from_model(cls, instances, model_path):
        tagger = crfsuite.Tagger()
        tagger.open(model_path)

        for identifier, xseq in cls.convert_to_crfsuite_instances(instances, False):
            tagger.set(xseq)
            yseq = tagger.viterbi()
            for t, y in enumerate(yseq):
                yield identifier, y, tagger.marginal(y, t)


    def evaluate(self, tag_seq, training_data):
        logging_fp = open(self.log_path, 'a')

        tagged_data = defaultdict(list)
        for identifier, subj, prob in tag_seq:
            tagged_data[identifier].append((subj, prob))

        consensus_data = defaultdict(list)
        for instance in training_data:
            for counter, (identifier, word, pos, subj) in enumerate(instance):
                consensus_data[identifier].append((counter, subj))

        aggregated_consensus_data = defaultdict(list)
        pdb.set_trace()
        for identifier in consensus_data:
            if identifier == 692:
                pdb.set_trace()
            totaler = Counter([i[0] for i in consensus_data[identifier]])
            subjer  = Counter([i[0] for i in consensus_data[identifier] if i[1] == 's'])
            for counter in sorted(totaler, reverse=True):
                subj = 'q'
                prob =  1.0*subjer[counter] / totaler[counter]
                if prob > 0.5:
                    subj = 's'
                aggregated_consensus_data[identifier].append((subj, prob))

        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0

        print >> logging_fp, "\n\n*********\n"
        print >> logging_fp, strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print >> logging_fp, "\n"
        for identifier in tagged_data:
            print >> logging_fp, identifier, '\t',
            print >> logging_fp, 'predicted', 'actual'

            actual_seq = ''.join(i[0] for i in aggregated_consensus_data[identifier])
            predicted  = ''.join(i[0] for i in tagged_data[identifier])

            print >> logging_fp, predicted, '\t'
            print >> logging_fp, actual_seq

            print >> logging_fp, "\nMore:"
            for actual, (predicted, prob) in zip(actual_seq, tagged_data[identifier]):
                print >> logging_fp, actual, predicted, prob
                if actual == predicted:
                    if actual == 's':
                        true_positives += 1
                    elif actual == 'q':
                        true_negatives += 1
                    else:
                        raise ValueError((actual, predicted))
                else:
                    if actual == 'q' and predicted == 's':
                        false_positives += 1
                    elif actual == 's' and predicted == 'q':
                        false_negatives += 1
                    else:
                        raise ValueError((actual, predicted))

            print >> logging_fp, "\n"

        print >> logging_fp, "\nSummary:"
        print >> logging_fp, "Precision: %.4f" % (true_positives * 1.0 / max(true_positives + true_negatives, 1),)
        print >> logging_fp, "Recall: %.4f" % (true_positives * 1.0 / max(true_positives + false_negatives, 1),)
        print >> logging_fp, "Accuracy: %.4f" % (1.0*(true_negatives + true_positives) / max(true_negatives + true_positives + false_negatives + false_positives, 1),)
        print >> logging_fp, "\n"
        logging_fp.close()

    def execute(self, path, conn):
        cursor = conn.cursor()
        subcursor = conn.cursor()

        if self.mode in ["train", "evaluate"]:
            cursor = conn.cursor()
            cursor.execute("""SELECT document_identifier,start,word,tag,synset,pos,neu,neg,total FROM pos_off_gimpel
                ORDER BY start ASC""")
            training_data = defaultdict(list)

            for identifier, start, word, tag, synset, pos, neu, neg, total in cursor.fetchall():
                output = word
                if synset is not None:
                    root, pos, sense = synset.split('.')
                    output = "%s.%s" % (root, sense)

                # Fetch subphrases
                cursor.execute("""SELECT annotation FROM subphrases WHERE document_identifier = ?""", (identifier,))
                for sentiment_ann, in cursor.fetchall():
                    pass

                cursor.execute("""SELECT document FROM pos_norm_gimpel WHERE document_identifier = ?""", (identifier,))
                for document, in cursor.fetchall():
                    pass

                document = document.split(' ')
                counter = 0
                buf = []
                for annotation, word in zip(sentiment_ann, document):
                    if annotation in ['p','n','e']:
                        annotation = u's'
                    buf.append((counter, annotation, word))
                    if counter >= start:
                        break
                    counter += len(word) + 1

                if identifier == 28:
                    import pprint
                    pprint.pprint(buf)
                    pprint.pprint(min(buf, key=lambda x: abs(x[0]-start)))
                    print counter, start, abs(counter-start)
                position, annotation, word = min(buf, key=lambda x: abs(x[0]-start))

                training_data[identifier].append((output, tag, annotation))


            training_buf = []
            for identifier in training_data:
                tmp = []
                for output, tag, annotation in training_data[identifier]:
                    tmp.append((identifier, output, tag, annotation))
                training_buf.append(tmp)

            # TODO: parameters
            #cursor.execute("""SELECT document_identifier, annotation FROM subphrases""")
            #training_buf = []
            #for identifier, annotation in cursor.fetchall():
            #    units = training_data[identifier]
            #    tmp = []
            #    for ann, (word, tag) in zip(annotation, units):
            #        if ann in ['p', 'n', 'e']:
            #            ann = u's'
            #        tmp.append((identifier, word, tag, ann))
            #    training_buf.append(tmp)

            self.train_and_output_model(training_buf, self.model_path)

        if self.mode in ["tag", "evaluate"]:
            cursor = conn.cursor()
            cursor.execute("""SELECT document_identifier,word,tag,synset FROM pos_off_gimpel
                ORDER BY start DESC""")
            testing_data = defaultdict(list)
            for identifier, word, tag, synset in cursor.fetchall():
                output = word
                if synset is not None:
                    root, pos, sense = synset.split('.')
                    output = "%s.%s" % (root, sense)
                testing_data[identifier].append((word, tag))

            testing_buf = []
            for identifier in testing_data:
                tmp = []
                for word, tag in testing_data[identifier]:
                    tmp.append((identifier, word, tag, None))
                testing_buf.append(tmp)

            tags = self.tag_instances_from_model(testing_buf, self.model_path)

            if self.mode == "evaluate":
                self.evaluate(tags, training_buf)


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

