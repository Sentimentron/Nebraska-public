#!/usr/bin/env python
"""
    Contains functions for standard word normalisation and stemming
"""
import re
import logging

from nltk.stem.lancaster import LancasterStemmer
from nltk.stem.porter import PorterStemmer
from nltk.stem.regexp import RegexpStemmer
from nltk.stem.snowball import EnglishStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet as wn
from itertools import chain

def xml_bool_convert(string):
    """
        Convert a standard XML "true" "false" value into
        a Python bool
    """
    if string is None:
        return False
    if string == "true":
        return True
    elif string == "false":
        return False
    else:
        raise ValueError(string)

class LeskStemmer(object):

    def __init__(self):
        self.ps = PorterStemmer()

    def lesk(self, context_sentence, ambiguous_word, pos, stem=True, hyperhypo=True):
        max_overlaps = 0
        lesk_sense = None

        if pos not in ["n", "z", "v", "a", "r"]:
            return pos

        for ss in wn.synsets(ambiguous_word):
            if ss.pos != pos:
                continue

            lesk_dictionary = []

            # Includes definition.
            lesk_dictionary+= ss.definition.split()
            # Includes lemma_names.
            lesk_dictionary+= ss.lemma_names

            # Optional: includes lemma_names of hypernyms and hyponyms.
            if hyperhypo == True:
                lesk_dictionary+= list(chain(*[i.lemma_names for i in ss.hypernyms()+ss.hyponyms()]))

            if stem == True: # Matching exact words causes sparsity, so lets match stems.
                lesk_dictionary = [self.ps.stem(i) for i in lesk_dictionary]
                context_sentence = [self.ps.stem(i) for i in context_sentence]

            overlaps = set(lesk_dictionary).intersection(context_sentence)

            if len(overlaps) > max_overlaps:
                lesk_sense = ss
                max_overlaps = len(overlaps)

        if lesk_sense is not None:
            lesk_sense = lesk_sense.name

        return lesk_sense

class SubjectiveWordNormaliser(object):
    """
        Exports subjectivity data to a CRF file for processing.
    """

    def __init__(self, xml):
        """
            Initialise the normaliser

            stemmer: Which NLTK-based stemmer to use
                Can use "lancaster", "regexp", "porter", "snowball"
            stopWords: Whether is_stop_word reports true or false
            stopPos: Whether is_stopped_pos reports true or false
            normaliseCase: convert everything to lower-case
            lemmatise: use Wordnet's morphy function to lemmatise
            normalisingRExp: replaces characters in the word according to this
        """
        # Normalisation parameters
        self.stemmer = xml.get("stemmer")
        self.stopwords = xml_bool_convert(xml.get("stopWords"))
        self.stoppos = xml_bool_convert(xml.get("stopPos"))
        self.normalise_case = xml_bool_convert(xml.get("normaliseCase"))
        self.lemmatise = xml_bool_convert(xml.get("lemmatise"))
        self.resub = xml.get("normalisingRExp")

        # Construct the right stemmer
        if self.stemmer is not None:
            assert self.stemmer in ["lancaster", "regexp", "porter", "snowball"]
            assert self.lemmatise == False
            if self.stemmer == "lancaster":
                self.stemmer = LancasterStemmer()
            elif self.stemmer == "regexp":
                self.stemmer = RegexpStemmer('ing$|s$|e$', min=4)
            elif self.stemmer == "porter":
                self.stemmer = PorterStemmer()
            elif self.stemmer == "snowball":
                self.stemmer = EnglishStemmer()
            elif self.stemmer == "lesk":
                self.stemmer = LeskStemmer()
            else:
                raise ValueError(("Unsupported stemmer", self.stemmer))

        # Construct the right lemmatiser
        if self.lemmatise:
            self.lemmatiser = WordNetLemmatizer()
        else:
            self.lemmatiser = None

    def is_stop_word(self, word):
        """
            Checks whether the word is part of a stop word, i.e. it's very common
            and not particularly meaningful.
        """
        # If we're not reporting stop words...
        if not self.stopwords:
            return False

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

    def is_stopped_pos_tag(self, tag):
        """
            Outputs True if the pos tag is stopped
        """
        if not self.stoppos:
            return False
        return tag in ["^", "!", "&", "L", "P", "O", "D", "$", ","]

    def stem_word(self, word):
        """
            Stems the word
        """
        return self.stemmer.stem(word)

    def lemmatise_word(self, word):
        """
            Lemmatise word
        """
        return self.lemmatiser.lemmatize(word)

    def normalise_output_word(self, word):
        """
            Apply transformations to the word, output result
        """
        if self.stopwords:
            if self.is_stop_word(word):
                return "STOPPED"
        if self.stemmer is not None:
            word = self.stem_word(word)
        elif self.lemmatise:
            word = self.lemmatise_word(word)

        if self.normalise_case:
            word = word.lower()

        if self.resub is not None:
            word = re.sub(self.resub, '', word)
            if len(word) == 0:
                word = "FILTERED"

        return word

