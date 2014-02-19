#!/usr/bin/env python

"""
    Code for interacting with CRFSuite
"""

import logging
import math
import re
import subprocess
import tempfile
from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator
from collections import defaultdict
from nltk.stem.lancaster import LancasterStemmer

class CRFSubjectiveExporter(HumanBasedSubjectivePhraseAnnotator):
    """
        Exports subjectivity data to a CRF file for processing.
    """

    def __init__(self, xml):
        """
            Path attribute is mandatory.
        """
        super(CRFSubjectiveExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        assert self.path is not None

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
            ret.append((identifier, text, probs))

        return ret

    @classmethod
    def load_pos_tokens(self, conn):
        """
            Create an token identifier -> token dict from the database
        """
        cursor = conn.cursor()
        cursor.execute("SELECT identifier, token FROM pos_tokens_gimpel")
        ret = {}
        for identifier, token in cursor.fetchall():
            ret[identifier] = token
        return ret

    @classmethod
    def load_pos_anns(self, conn):
        """
            Load part-of-speech annotations from the database.
            Only the gimpel POS tagger is supported at present.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT document_identifier, tokenized_form FROM pos_gimpel")
        ret = {}
        for identifier, tokenised in cursor.fetchall():
            ret[identifier] = [int(i) for i in tokenised.split(' ') if len(i) > 0]
        return ret

    @classmethod
    def is_stop_word(self, word):
        """
            Checks whether the word is part of a stop word, i.e. it's very common
            and not particularly meaningful.
        """
        stopwords = """a,able,about,across,after,all,almost,also,am
        ,among,an,and,any,are,as,at,be,because
        ,been,but,by,can,cannot,could,dear
        ,did,do,does,either,else,ever,every
        ,for,from,get,got,had,has,have,he,her
        ,hers,him,his,how,however,i,if,in,into
        ,is,it,its,just,least,let,like,likely,
        may,me,might,most,must,my,neither,no,nor,
        not,of,off,often,on,only,or,other,our,own,
        rather,said,say,says,she,should,since,so,
        some,than,that,the,their,them,then,there,
        these,they,this,tis,to,too,twas,us,wants,
        was,we,were,what,when,where,which,while,
        who,whom,why,will,with,would,yet,you,your""".split(",")
        stopwords = [i.strip() for i in stopwords]
        return word.lower() in stopwords

    @classmethod
    def is_stopped_pos_tag(self, tag):
        """
            Controls whether the subjectivity tag '0' is output
        """
        return tag in ["^", "!", "&", "L","P", "O", "D", "$", ","]

    @classmethod
    def convert_annotation(cls, ann):
        """
            Converts the annotation into a 1 or 0 label,

                1 implies some subjectivity (greater than 10% of people said
                    it was subjective)
                0 implies less than 10% of annotations thought it was subjective
        """
        ann -= 0.001
        ann = max(ann, 0)
        ann = int(math.floor(ann*10))
        if ann >= 1:
            return '1'
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
            for identifier in documents:
                text = documents[identifier]
                postokens = anns[identifier]
                # Convert the pos token identifiers to the
                # actual pos strings
                postokens = [tokens[i] for i in postokens]
                # Split the document in the same way as done
                # for the annotations in the MT form
                text = text.split(' ')
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
                        pos,_,pos_word = next_pos_tag.partition('/')
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
                        pos,_,pos_word = next_pos_tag.partition('/')
                        end_pos_range += 1

                    # Correct post-increment
                    end_pos_range = max(end_pos_range-1, 0)

                    # If we didn't find the starting tag, then our
                    # POS-tag matching will be hopelessly wrong and
                    # we might as well stop.
                    if output == False:
                        logging.warning(("Couldn't match up the POS tokens: %s (%s)", text, postokens))
                        continue

                    # Otherwise, output each POS-tagged word and the appropriate annotation
                    for i in range(start_pos_range, end_pos_range):
                        previous_pos_tag = i
                        next_pos_tag = postokens[i]
                        pos,_,pos_word = next_pos_tag.partition('/')
                        # Output the word associated with the POS tag
                        output_fp.write("%s " % (pos_word.lower(),))
                        # Output the the word associated with this POS tag
                        output_fp.write("%s " % (pos, ))
                        # Output all the possibile subjective annotations for the
                        # text unit (approximate word) which contains this POS tag
                        for p in possibilities[t]:
                            output_fp.write(p)
                            output_fp.write(" ")
                        # End this entry
                        output_fp.write("\n")

                # Output the document-separating line space
                output_fp.write("\n")

        return True, conn

class ProduceCRFSTagList(object):

    def __init__(self, xml):
        self.test_path = xml.get("test_path")
        self.train_path = xml.get("train_path")
        assert self.test_path is not None
        assert self.train_path is not None

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
                    args = "crfsuite learn --split=10 -m %s %s"
                    subprocess.check_call(args % (model_fp.name, train_dest_fp.name), shell=True)

                    # Test the model
                    args = "crfsuite tag -qt -m %s %s"
                    subprocess.check_call (args % (model_fp.name, test_dest_fp.name), shell=True)

                    with open('crf_results.txt', 'w') as out_fp:
                        # Tag the output
                        args = "crfsuite tag -m %s %s"
                        subprocess.check_call(args % (model_fp.name, test_dest_fp.name), shell=True, stdout=out_fp)

                    logging.debug("%s %s %s", train_dest_fp.name, test_dest_fp.name, model_fp.name)

        return True, conn