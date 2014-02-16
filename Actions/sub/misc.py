#!/bin/env python

"""
    Contains classes which don't really fit anywhere else in this module
"""
import re
import math
import logging
from human import HumanBasedSubjectivePhraseAnnotator
from collections import defaultdict

from nltk.stem.lancaster import LancasterStemmer

class MQPASubjectivityReader(object):
    def __init__(self, path="Data/subjclueslen1-HLTEMNLP05.tff"):
        self.data = {}
        with open(path, 'rU') as src:
            for line in src:
                line = line.strip()
                atoms = line.split(' ')
                row = {i:j for i, _, j in [a.partition('=') for a in atoms]}
                logging.debug(row)
                self.data[row["word1"]] = row

    def get_subjectivity_pairs(self, strong_strength, weak_strength):
        for word in self.data:
            strength = weak_strength
            if self.data[word]['type'] == 'strongsubj':
                strength = strong_strength
            yield (word, strength)

class CRFSubjectiveExporter(HumanBasedSubjectivePhraseAnnotator):

    def __init__(self, xml):
        super(HumanBasedSubjectivePhraseAnnotator, self).__init__(
            xml
        )

        self.path = xml.get("path")
        assert self.path is not None

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
            ret.append((identifier, text, probs))

        return ret

    @classmethod
    def load_pos_tokens(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT identifier, token FROM pos_tokens_gimpel")
        ret = {}
        for identifier, token in cursor.fetchall():
            ret[identifier] = token
        return ret

    @classmethod
    def load_pos_anns(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT document_identifier, tokenized_form FROM pos_gimpel")
        ret = {}
        for identifier, tokenised in cursor.fetchall():
            ret[identifier] = [int(i) for i in tokenised.split(' ') if len(i) > 0]
        return ret

    @classmethod
    def is_stop_word(self, word):
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
        return tag in ["^", "!", "&", "L","P", "O", "D", "$", ","]

    @classmethod
    def convert_annotation(cls, ann):
        ann -= 0.001
        ann = max(ann, 0)
        ann = int(math.floor(ann*10))
        if ann >= 1:
            return '1'
        else:
            return '0'

    def execute(self, path, conn):
        annotations = self.group_and_convert_text_anns(conn)
        possibilities = defaultdict(set)
        documents = {}
        identifier_anns = {}
        tokens = self.load_pos_tokens(conn)
        anns = self.load_pos_anns(conn)

        for identifier, text, annotation in annotations:
            documents[identifier] = text
            text = text.split(' ')
            for i, j in zip(text, annotation):
                possibilities[i].add(j)

        with open(self.path, 'w') as output_fp:
            for identifier in documents:
                text = documents[identifier]
                postokens = anns[identifier]
                postokens = [tokens[i] for i in postokens]
                logging.debug(postokens)
                text = text.split(' ')
                current_pos_tag = 0
                previous_pos_tag = 0
                current_word = 0
                # Step through each word in the tweet
                for t in text:
                    pos_word = "ASDFASDFASDF"
                    start_pos_range = previous_pos_tag
                    output = True

                    while pos_word not in t:
                        #logging.debug((pos_word, t, start_pos_range, postokens))
                        if start_pos_range >= len(postokens):
                            output = False
                            break
                        next_pos_tag = postokens[start_pos_range]
                        pos,_,pos_word = next_pos_tag.partition('/')
                        start_pos_range += 1

                    start_pos_range = max(start_pos_range-1, 0)
                    end_pos_range = start_pos_range

                    while pos_word in t:
                        #logging.debug((pos_word, t, end_pos_range))
                        #logging.debug((end_pos_range, len(postokens)))
                        if end_pos_range >= len(postokens):
                            end_pos_range = len(postokens) + 1
                            break
                        next_pos_tag = postokens[end_pos_range]
                        pos,_,pos_word = next_pos_tag.partition('/')
                        end_pos_range += 1

                    end_pos_range = max(end_pos_range-1, 0)

                    if output == False:
                        logging.warning(("Couldn't match up the POS tokens: %s (%s)", text, postokens))
                        continue

                    for i in range(start_pos_range, end_pos_range):
                        previous_pos_tag = i
                        next_pos_tag = postokens[i]
                        pos,_,pos_word = next_pos_tag.partition('/')
                        logging.debug((i, start_pos_range, end_pos_range, pos, pos_word, t))
                        output_fp.write("%s " % (pos_word.lower(),))
                        output_fp.write("%s " % (pos, ))
                        for p in possibilities[t]:
                            output_fp.write(p)
                            output_fp.write(" ")
                        output_fp.write("\n")
                    output_fp.write("\n")

        return True, conn