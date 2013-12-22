#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import logging
import nltk

class WorkflowNativePOSTagger(object):

    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
        self.verbose = xml.get("verbose")
        if self.verbose is None:
            self.verbose = False
        else:
            self.verbose = True

    def execute(self, path, conn):
        # Select the input documents
        c = conn.cursor()
        sql = "SELECT COUNT(*) FROM input"
        c.execute(sql)
        (number_of_rows, ) = c.fetchone()
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        # TO DO: Get current tags from the database
        # conn.row_factory = dict_factory
        # c.execute("SELECT identifier, token FROM pos_tokens_%s" % self.dest)
        # tokens = c.fetchall()
        tokens = {}
        documents = {}
        for counter, (identifier, document) in enumerate(c.fetchall()):
            tagged_string = ""
            tagged_form = []
            if self.verbose:
                logging.debug("%.2f %% done", counter * 100.0 / number_of_rows)
            for token in self.tokenize(document):
                # Check if this this token was in the database already
                if token in tokens:
                    tagged_form.append(tokens[token])
                else:
                    # Insert the new tag in the database
                    c.execute("INSERT INTO pos_tokens_%s(token) VALUES (?)" % self.dest, [token])
                    # Add it to the dictionary
                    tokens[token] = c.lastrowid
                    tagged_form.append(c.lastrowid)
                    #tagged_string = tagged_string + "[" +`tokens[token]`+"] "
            # Convert into tagged string
            tagged_string = ' '.join("%d" % (t) for t in tagged_form)
            # Insert this string which has been converted into tags into the db
            c.execute("INSERT INTO pos_%s(document_identifier, tokenized_form) VALUES (?, ?)" % self.dest, (identifier, tagged_string))
        logging.info("Committing changes...")
        conn.commit()
        return True, conn

class WhiteSpacePOSTagger(WorkflowNativePOSTagger):

    def __init__(self, xml):
        super(WhiteSpacePOSTagger, self).__init__(xml)
        self.permitted = set(string.letters + '#' + '@')

    def sanitize(self, token):
        end_position = len(token)
        # Seek through reversed string, trim punctuation at end
        for c, i in enumerate(token):
            if i not in self.permitted:
                end_position = c
                break
        # If it's all punctuation, may be an emoticon
        if end_position == 0:
            return token

        return token[0:end_position]

    def tokenize(self, document):
        tokens = document.split(" ")
        tokens = [t.lower() for t in tokens]
        tokens = [self.sanitize(t) for t in tokens]
        tokens = [t for t in tokens if len(t) > 0]
        return tokens

class NLTKPOSTagger(WorkflowNativePOSTagger):

    def __init__(self, xml):
        import nltk.data
        import nltk.tag
        super(NLTKPOSTagger, self).__init__(xml)
        self.tagger = nltk.data.load(nltk.tag._POS_TAGGER)

    def tokenize(self, document):
        # Make sure to run nltk.download('maxent_treebank_pos_tagger') first, you'll also need numpy
        tokens = nltk.word_tokenize(document)
        for word, tag in self.tagger.tag(tokens):
            yield "%s/%s" % (word, tag)

class StanfordTagger(WorkflowNativePOSTagger):

    def __init__(self, xml):
        from nltk.tag.stanford import POSTagger
        import os
        super(StanfordTagger, self).__init__(xml)
        self.tagger = POSTagger(os.path.join(os.getcwd(),'External/english-bidirectional-distsim.tagger'), os.path.join(os.getcwd(),'External/stanford-postagger.jar'))

    def is_ascii(self, s):
        return all(ord(c) < 128 for c in s)

    def tokenize(self, document):
        # Non ASCII characters makes the stanford tagger go crazy and run out of heap space
        if self.is_ascii(document):
            for word, tag in self.tagger.tag(document):
                    yield "%s/%s" % (word, tag)


