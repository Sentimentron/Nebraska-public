#!/usr/bin/env python

"""
    Contains classes for working with WEKA IO for exploration.
"""
from __future__ import division
import re
import csv
import logging
import pprint
from itertools import groupby, chain
from collections import defaultdict, Counter, OrderedDict
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.snowball import EnglishStemmer
from Actions.sub.word import SubjectiveWordNormaliser
from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator

class ARFFExporter(object):

    def __init__(self, path, name):
        self.path = path
        self.attributes = OrderedDict()
        self.name = name

    def add_attribute(self, name, kind):
        self.attributes[name] = kind

    def write(self, rows):
        with open(self.path, 'w') as output_file:
            print >> output_file, "@relation", self.name
            print >> output_file, ""
            for name in self.attributes:
                print >> output_file, "@attribute", name,
                kind = self.attributes[name]
                if type(kind) == type([]):
                    fmt = "{%s}" % (','.join(kind),)
                    print >> output_file, fmt
                else:
                    print >> output_file, kind
            print >> output_file, ""
            print >> output_file, "@data"
            writer = csv.writer(output_file)
            for row in rows:
                if len(row) != len(self.attributes):
                    logging.error((len(row), len(self.attributes)))
                    continue
                writer.writerow(row)

class BigramBinaryPresenceTotalNumberSubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(BigramBinaryPresenceTotalNumberSubjectiveARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of bigram occurences
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
                if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                    continue
                bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
                if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
                if bigram in counts:
                    counts[bigram] += 1
                else:
                    counts[bigram] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
               bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
               if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                   continue
               if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                   continue
               if self.stem:
                  bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
               if self.lemmise:
                  bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
               if self.threshold:
                   if counts[bigram] < self.threshold:
                       continue
               words.add(bigram)

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("num_subjective", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for i in range(1,len(text)-1):
                bigram = text[i].lower() + "-" + text[i+1].lower()
                if len(text[i]) == 0 or len(text[i+1]) == 0 or text[i] == ' ' or text[i+1] == ' ':
                    continue
                if(self.use_stop_words and (text[i].lower() in stopwords or text[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(text[i].lower()) + "-" + EnglishStemmer().stem(text[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(text[i].lower()) + "-" + WordNetLemmatizer().lemmatize(text[i+1].lower())
                if self.threshold:
                    if counts[bigram] < self.threshold:
                        continue
                # And set it to present
                row[word_ids[bigram]] = 1
            # Throw this row in the result
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            number_positive = len(re.findall("p+p", annotation))
            number_negative = len(re.findall("n+n", annotation))
            number_neutral = len(re.findall("e+e", annotation))
            number_subjective = number_positive + number_negative + number_neutral
            row.append(number_subjective)

            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class BigramBinaryPresenceNumberSubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(BigramBinaryPresenceNumberSubjectiveARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of bigram occurences
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
                if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                    continue
                bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
                if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
                if bigram in counts:
                    counts[bigram] += 1
                else:
                    counts[bigram] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
               bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
               if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                   continue
               if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                   continue
               if self.stem:
                  bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
               if self.lemmise:
                  bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
               if self.threshold:
                   if counts[bigram] < self.threshold:
                       continue
               words.add(bigram)

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("num_positive", 'numeric')
        self.exporter.add_attribute("num_negative", 'numeric')
        self.exporter.add_attribute("num_neutral", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for i in range(1,len(text)-1):
                bigram = text[i].lower() + "-" + text[i+1].lower()
                if len(text[i]) == 0 or len(text[i+1]) == 0 or text[i] == ' ' or text[i+1] == ' ':
                    continue
                if(self.use_stop_words and (text[i].lower() in stopwords or text[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(text[i].lower()) + "-" + EnglishStemmer().stem(text[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(text[i].lower()) + "-" + WordNetLemmatizer().lemmatize(text[i+1].lower())
                if self.threshold:
                    if counts[bigram] < self.threshold:
                        continue
                # And set it to present
                row[word_ids[bigram]] = 1
            # Throw this row in the result
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            number_positive = len(re.findall("p+p", annotation))
            number_negative = len(re.findall("n+n", annotation))
            number_neutral = len(re.findall("e+e", annotation))
            row.append(number_positive)
            row.append(number_negative)
            row.append(number_neutral)

            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class BigramBinaryPresencePercentageSubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(BigramBinaryPresencePercentageSubjectiveARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of bigram occurences
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
                if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                    continue
                bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
                if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
                if bigram in counts:
                    counts[bigram] += 1
                else:
                    counts[bigram] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
               bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
               if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                   continue
               if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                   continue
               if self.stem:
                  bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
               if self.lemmise:
                  bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
               if self.threshold:
                   if counts[bigram] < self.threshold:
                       continue
               words.add(bigram)

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("percent_positive", 'numeric')
        self.exporter.add_attribute("percent_negative", 'numeric')
        self.exporter.add_attribute("percent_neutral", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for i in range(1,len(text)-1):
                bigram = text[i].lower() + "-" + text[i+1].lower()
                if len(text[i]) == 0 or len(text[i+1]) == 0 or text[i] == ' ' or text[i+1] == ' ':
                    continue
                if(self.use_stop_words and (text[i].lower() in stopwords or text[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(text[i].lower()) + "-" + EnglishStemmer().stem(text[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(text[i].lower()) + "-" + WordNetLemmatizer().lemmatize(text[i+1].lower())
                if self.threshold:
                    if counts[bigram] < self.threshold:
                        continue
                # And set it to present
                row[word_ids[bigram]] = 1
            # Throw this row in the result
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            percent_positive = annotation.count('p') / len(text)
            percent_negative = annotation.count('n') / len(text)
            percent_neutral = annotation.count('e') / len(text)
            row.append(percent_positive)
            row.append(percent_negative)
            row.append(percent_neutral)

            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class BigramBinaryPresenceARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(BigramBinaryPresenceARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of bigram occurences
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
                if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                    continue
                bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
                if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
                if bigram in counts:
                    counts[bigram] += 1
                else:
                    counts[bigram] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            tweet_split = text.split(' ')
            for i in range(1,len(tweet_split)-1):
                bigram = tweet_split[i].lower() + "-" + tweet_split[i+1].lower()
                if len(tweet_split[i]) == 0 or len(tweet_split[i+1]) == 0 or tweet_split[i] == ' ' or tweet_split[i+1] == ' ':
                    continue
                if(self.use_stop_words and (tweet_split[i].lower() in stopwords or tweet_split[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(tweet_split[i].lower()) + "-" + EnglishStemmer().stem(tweet_split[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(tweet_split[i].lower()) + "-" + WordNetLemmatizer().lemmatize(tweet_split[i+1].lower())
                if self.threshold:
                    if counts[bigram] < self.threshold:
                        continue
                words.add(bigram)

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for i in range(1,len(text)-1):
                bigram = text[i].lower() + "-" + text[i+1].lower()
                if len(text[i]) == 0 or len(text[i+1]) == 0 or text[i] == ' ' or text[i+1] == ' ':
                    continue
                if(self.use_stop_words and (text[i].lower() in stopwords or text[i+1].lower() in stopwords)):
                    continue
                if self.stem:
                    bigram = EnglishStemmer().stem(text[i].lower()) + "-" + EnglishStemmer().stem(text[i+1].lower())
                if self.lemmise:
                    bigram = WordNetLemmatizer().lemmatize(text[i].lower()) + "-" + WordNetLemmatizer().lemmatize(text[i+1].lower())
                if self.threshold:
                    if counts[bigram] < self.threshold:
                        continue
                # And set it to present
                row[word_ids[bigram]] = 1
            # Throw this row in the result
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class UnigramBinaryPresenceWithTotalNumberOfSubjectivePhrasesARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(UnigramBinaryPresenceWithTotalNumberOfSubjectivePhrasesARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of occurences of each unigram
        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                elif word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And add it as an attribute
                words.add(word.lower())

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("number_of_subjective_phrases", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for word in text:
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                if len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And set it to present
                row[word_ids[word]] = 1
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            number_positive = len(re.findall("p+p", annotation))
            number_negative = len(re.findall("n+n", annotation))
            number_neutral = len(re.findall("e+e", annotation))
            total_phrases = number_positive + number_negative + number_neutral
            row.append(total_phrases)

            # Throw this row in the result
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class UnigramBinaryPresenceWithNumberOfSubjectivePhrasesARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(UnigramBinaryPresenceWithNumberOfSubjectivePhrasesARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of occurences of each unigram
        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                elif word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And add it as an attribute
                words.add(word.lower())

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("number_positive", 'numeric')
        self.exporter.add_attribute("number_negative", 'numeric')
        self.exporter.add_attribute("number_neutral", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for word in text:
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                if len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And set it to present
                row[word_ids[word]] = 1
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            number_positive = len(re.findall("p+p", annotation))
            number_negative = len(re.findall("n+n", annotation))
            number_neutral = len(re.findall("e+e", annotation))
            row.append(number_positive)
            row.append(number_negative)
            row.append(number_neutral)

            # Throw this row in the result
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class UnigramBinaryPresenceWithPercentageSubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def getAnnotation(self, conn, identifier):
        cursor = conn.cursor()
        result = cursor.execute("SELECT annotation FROM subphrases WHERE document_identifier = ?", (identifier,))
        result = result.fetchone()
        return result[0]

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(UnigramBinaryPresenceWithPercentageSubjectiveARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of occurences of each unigram
        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                elif word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And add it as an attribute
                words.add(word.lower())

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the percentage pos, neg and neutral attributes
        self.exporter.add_attribute("percent_positive", 'numeric')
        self.exporter.add_attribute("percent_negative", 'numeric')
        self.exporter.add_attribute("percent_neutral", 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for word in text:
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                if len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And set it to present
                row[word_ids[word]] = 1
            # Now calculate the percentages of positive negative and neutral
            annotation = self.getAnnotation(conn, identifier)
            percent_positive = annotation.count('p') / len(text)
            percent_negative = annotation.count('n') / len(text)
            percent_neutral = annotation.count('e') / len(text)
            row.append(percent_positive)
            row.append(percent_negative)
            row.append(percent_neutral)

            # Throw this row in the result
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class UnigramBinaryPresenceARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (id, text, annnotation) triples
        """
        cursor = conn.cursor()
        ret = []
        # Get all the tweets from the database
        sql = """SELECT input.document, subphrases.sentiment FROM input JOIN subphrases ON input.identifier = subphrases.document_identifier WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            # For every tweet and its annotation
            for text, sentiment in cursor.fetchall():
                # Ditch anything thats not a letter
                text = re.sub('[^a-zA-Z ]', '', text)
                # And return the identifier, the tweet and its overall sentiment
                ret.append((identifier, text, sentiment))
        return ret

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(UnigramBinaryPresenceARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        self.threshold = xml.get("threshold")
        self.stem = xml.get("stem")
        self.lemmise = xml.get("lemmise")
        if self.threshold is not None:
            self.threshold = int(self.threshold)
        if self.stem != "true":
            self.stem = False
        else:
            self.stem = True
        if self.lemmise != "true":
            self.lemmise = False
        else:
            self.lemmise = True
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
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

        # Get all the tweets from the database
        data = self.get_text_anns(conn)
        words = set([])
        counts = {}

        # Count the number of occurences of each unigram
        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                elif word in counts:
                    counts[word] += 1
                else:
                    counts[word] = 1

        # For every tweet we got back
        for identifier, text, sentiment in data:
            # Split it on white space
            for word in text.split(' '):
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                elif len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And add it as an attribute
                words.add(word.lower())

        # Add all these unigrams as attributes in the arff file with possible values of 0 and 1
        for word in sorted(words):
            self.exporter.add_attribute(word, 'numeric')
        # Add the overall sentiment of the tweet as a nominal attribute
        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        # Get a dictionary mapping the words that are our attributes to integers that represent their index in the ARFF file
        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        # For each tweet in our database
        for identifier, text, sentiment in data:
            # Split it on white space
            text = text.split(' ')
            # Set every attribute in the row to not present
            row = [0 for _ in words]
            # Itterate over each word in the tweet
            for word in text:
                word = word.lower()
                if self.use_stop_words and word in stopwords:
                    continue
                if len(word) == 0:
                    continue
                if self.threshold:
                    if counts[word] < self.threshold:
                        continue
                if self.stem:
                    word = EnglishStemmer().stem(word)
                if self.lemmise:
                    word = WordNetLemmatizer().lemmatize(word)
                # And set it to present
                row[word_ids[word]] = 1
            # Throw this row in the result
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn

class SubjectivePhraseTweetClassficationDiscreteARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def get_text_anns(self, conn):
        """
            Generate a list of (text, annnotation) pairs
        """
        cursor = conn.cursor()
        ret = []
        sql = """SELECT input.document, subphrases.annotation, subphrases.sentiment
        FROM input JOIN subphrases
        ON input.identifier = subphrases.document_identifier
        WHERE input.identifier = ?"""
        for identifier in self.generate_source_identifiers(conn):
            cursor.execute(sql, (identifier,))
            for text, anns, sentiment in cursor.fetchall():
                text = re.sub('[^a-zA-Z ]', '', text)
                ret.append((identifier, text, anns, sentiment))
        return ret

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(SubjectivePhraseTweetClassficationDiscreteARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    def execute(self, path, conn):
        """

        """

        data = self.get_text_anns(conn)
        words = set([])

        for identifier, text, anns, sentiment in data:
            for word in text.split(' '):
                if len(word) == 0:
                    continue
                words.add(word.lower())

        for word in sorted(words):
            self.exporter.add_attribute(word, ["p", "n", "e", "q"])

        self.exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        word_ids = {w: i for i, w in enumerate(sorted(words))}

        rows = []
        for identifier, text, anns, sentiment in data:
            text = text.split(' ')
            row = ['q' for _ in words]
            for word, annotation in zip(text, [i for i in anns]):
                word = word.lower()
                if len(word) == 0:
                    continue
                row[word_ids[word]] = annotation
            row.append(sentiment)
            rows.append(row)

        self.exporter.write(rows)

        return True, conn


class SubjectivePhraseTweetClassificationARFFExporter(HumanBasedSubjectivePhraseAnnotator):
    """
        Create an ARFF file to test feature selection for subjective phrases

            Counts the maximum number of subjective phrases which occur in any annotation
            of any tweet. [count_subphrases]

            Finds all the regions for every tweet which someone annotated as subjective
                [collect_membership_annotations]

            For each tweet
                For each possible subjective region
                    Computes the proportion of people who highlighted this section

            For each tweet
                For each possible subjective region
                    Computes the proportion of people who highlighted any part of the region
                        Positive, neutral, negative
    """

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute
        """
        super(SubjectivePhraseTweetClassificationARFFExporter, self).__init__(
            xml
        )

        self.path = xml.get("path")
        self.exporter = ARFFExporter(self.path, "tweet_sentiment")
        self.use_stop_words = xml.get("useStopWords")
        if self.use_stop_words != "true":
            self.use_stop_words = False
        else:
            self.use_stop_words = True
        assert self.path is not None

    @classmethod
    def pad_annotation(cls, ann, length):
        return ann.ljust(length, 'q')

    @classmethod
    def annotation_is_member(cls, ann):
        return ann in ['n', 'e', 'p']

    @classmethod
    def summarize_annotation_info_over_tweet(cls, normalised_annotations):
        number_of_annotations = len(normalised_annotations)
        annotation_contribution = 1 / float(number_of_annotations)
        max_annotation_length = max([len(a) for a in normalised_annotations])
        ret = [0.0 for _ in range(max_annotation_length)]
        for annotation in normalised_annotations:
            for index, subjective in enumerate(annotation):
                if subjective:
                    ret[index] += annotation_contribution
        return ret


    @classmethod
    def process_annotation(cls, annotation, func):
        return [func(i) for i in annotation]

    @classmethod
    def load_annotations(cls, conn):
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
            if len(popular) > 1:
                _, pop2 = popular[1]
                if pop1 == pop2:
                    # No consensus, skip
                    continue
            ret[identifier] = label1
        return ret

    @classmethod
    def supress_stop_words(cls, text, annotations):
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
        annotations_ret = []
        text = [i.trim() for i in text.split(' ')]
        for word, annotation in zip(text, annotations):
            if len(word) == 0:
                annotations_ret.append(0.0)
                continue
            word = word.lower()
            word = re.sub('[^a-z]', '', word)
            if word in stopwords:
                annotations_ret.append(0.0)
            else:
                annotations_ret.append(annotation)
        return annotations_ret



    def produce_tweet_values(self, text, annotations):

        # Get annotation vectors
        membership_annotations = [self.process_annotation(i, lambda x: x in ['n', 'e', 'q']) for i in annotations]
        positive_annotations = [self.process_annotation(i, lambda x: x == 'p') for i in annotations]
        neutral_annotations = [self.process_annotation(i, lambda x: x == 'e') for i in annotations]
        negative_annotations = [self.process_annotation(i, lambda x: x== 'n') for i in annotations]

        logging.debug((membership_annotations, annotations))

        ret = []
        buf = defaultdict(list)
        subphrase_length = 0
        membership_vector = self.summarize_annotation_info_over_tweet(membership_annotations)
        positive_annotations = self.summarize_annotation_info_over_tweet(positive_annotations)
        neutral_annotations = self.summarize_annotation_info_over_tweet(neutral_annotations)
        negative_annotations = self.summarize_annotation_info_over_tweet(negative_annotations)

        if self.use_stop_words:
            membership_vector = self.suppress_stop_words(text, annotations)

        for index, i in enumerate(membership_vector):
            if abs(i - 0.0005) < 0.005:
                if subphrase_length > 0:
                    appendbuf = {}
                    for b in ["membership", "positive", "negative", "neutral"]:
                        logging.debug(("BUF", buf))
                        appendbuf[b] = sum(buf[b]) / float(subphrase_length)
                    appendbuf["count"] = subphrase_length
                    ret.append(appendbuf)
                    subphrase_length = 0
                    buf = defaultdict(list)
                continue

            buf["membership"].append(i)
            buf["positive"].append(positive_annotations[index])
            buf["neutral"].append(neutral_annotations[index])
            buf["negative"].append(negative_annotations[index])
            subphrase_length += 1
            buf["count"] = subphrase_length

        if subphrase_length > 0:
            appendbuf = {}
            for b in ["membership", "positive", "negative", "neutral"]:
                logging.debug(("BUF", buf))
                appendbuf[b] = sum(buf[b]) / float(subphrase_length)
            appendbuf["count"] = subphrase_length
            ret.append(appendbuf)

        return ret

    def execute(self, path, conn):
        data = self.get_text_anns(conn)
        labels = self.load_annotations(conn)

        identifier_text = {}
        identifier_anns = defaultdict(list)
        anns_summary = {}
        for identifier, text, anns in data:
            identifier_text[identifier] = text
            identifier_anns[identifier].append(anns)

        for identifier in identifier_text:
            if len(identifier_anns[identifier]) == 0:
                continue
            summary = self.produce_tweet_values(identifier_text[identifier], identifier_anns[identifier])
            if len(summary) == 0:
                logging.error(("FAILURE TO GENERATE SUMMARY", identifier_anns[identifier]))
                continue
            pprint.pprint(summary)
            anns_summary[identifier] = summary

        max_subphrases = 0
        for a in anns_summary:
            for i in anns_summary[a]:
                max_subphrases = max(max_subphrases, len(i))


        for i in range(max_subphrases):
            i += 1
            self.exporter.add_attribute("subjective_%d" % (i,), "numeric")
            self.exporter.add_attribute("positive_%d" % (i,), "numeric")
            self.exporter.add_attribute("neutral_%d" % (i,), "numeric")
            self.exporter.add_attribute("negative_%d" % (i,), "numeric")
            #self.exporter.add_attribute("subjective_%d" % (i,), "numeric")

        self.exporter.add_attribute("overall", ["positive", "negative", "neutral", "noconsensus"])

        rows = []
        for a in anns_summary:
            row = []
            for i in range(max_subphrases):
                if i < len(anns_summary[a]):
                    row.append(anns_summary[a][i]["membership"])
                    row.append(anns_summary[a][i]["positive"])
                    row.append(anns_summary[a][i]["neutral"])
                    row.append(anns_summary[a][i]["negative"])
                else:
                    row.extend([0.0,0.0,0.0,0.0])
            if a not in labels:
                row.append("noconsensus")
            else:
                row.append(labels[a])
            rows.append(row)

        self.exporter.write(rows)

        return True, conn


class SubjectivePhraseARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute.
        """
        super(SubjectivePhraseARFFExporter, self).__init__(
            xml
        )
        self.path = xml.get("path")
        self.export_presence = xml.get("exportPresence")
        self.export_subjectivity = xml.get("exportSubjectivity")
        if self.export_presence == "true":
            self.export_presence = True
        else:
            self.export_presence = False
        if self.export_subjectivity == "false":
            self.export_subjectivity = False
        else:
            self.export_subjectivity = True
        assert self.path is not None

    @classmethod
    def return_majority(cls, ann):
        counter = Counter(ann)
        popular = counter.most_common(2)
        ann1, pop1 = popular[0]
        if len(popular) > 1:
            ann2, pop2 = popular[1]
            if pop1 == pop2:
                # No consensus
                return None
        return ann1

    @classmethod
    def annotation_is_member(cls, ann):
        if ann in ['n', 'e', 'p']:
            return 's'
        else:
            return 'q'

    @classmethod
    def pad_annotation(cls, ann, length):
        return ann.ljust(length, 'q')

    @classmethod
    def santize_tweet(cls, tweet):
        text = text.split(' ')
        first = True
        word_anns = {}
        for ann, word in zip(anns, text):
            if len(word) == 0:
                continue
            if word[0].lower() != word[0] and not first:
                continue
            first = False
            word = word.lower()
            word = re.sub('[^a-z]', '', word)

    @classmethod
    def return_phrase_summary(cls, annotations):

        def select_column(which, data):
            for i in data:
                yield i[which]

        ret = {}
        # Pad annotations to the maximum length
        max_annotation_length = max([len(i) for i in annotations])
        logging.debug(("MAX_ANN_LEN", max_annotation_length))
        annotations = [cls.pad_annotation(i, max_annotation_length) for i in annotations]
        logging.debug(("PADDED_ANNOTATIONS", annotations))
        # Compute word membership
        memberships = [[cls.annotation_is_member(i) for i in j] for j in annotations]
        logging.debug(("WORD_MEMBERSHIPS", memberships))
        # Compute consensus
        cmembers = [cls.return_majority(select_column(i, memberships)) for i in range(max_annotation_length)]
        logging.debug(("CMEMBERS", cmembers))
        csentiment = [cls.return_majority(select_column(i, annotations)) for i in range(max_annotation_length)]
        logging.debug(("CSENTIMENT",csentiment))

        return cmembers, csentiment

    def convert_group_annotations(self, conn):
        data = self.get_text_anns(conn)
        annotations = {}
        identifier_text = {}
        ret = []
        for identifier, text, ann in data:
            identifier_text[identifier] = text
            if identifier not in annotations:
                annotations[identifier] = []
            annotations[identifier].append(ann)

        majority_annotations = {}
        for identifier in annotations:
            cmembers, csentiment = self.return_phrase_summary(annotations[identifier])
            # Find the subjective phrases within the consensus
            phrases = self.find_subjective_phrases(cmembers)
            logging.debug(phrases)
            for phrase in phrases:
                # Find the majority annotation for this sub-phrase
                logging.debug(("PHRASES", phrase))
                words_in_phrase = [identifier_text[identifier][i] for i in phrase]
                logging.debug(("WORDS_IN_PHRASE", words_in_phrase))

    @classmethod
    def find_subjective_phrases(cls, annotations):
        ret = []
        last = ''
        buf = []
        for index, i in enumerate(annotations):
            if i != last:
                if i == 'q':
                    # No longer in a subjective phrase
                    ret.append(buf)
                    buf = []
                    continue
            if i != 'q':
                buf.append(index)
        ret.append(buf)
        ret = [i for i in ret if len(i) > 0]
        logging.debug(("SUBJECTIVE_PHRASES", annotations, ret))
        return ret


    def execute(self, path, conn):
        self.convert_group_annotations(conn)
        return True, conn

class SubjectiveWordARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    def __init__(self, xml):
        super(SubjectiveWordARFFExporter, self).__init__(xml)
        self.normaliser = SubjectiveWordNormaliser(xml)
        self.path = xml.get("path")
        assert self.path is not None

    @classmethod
    def load_annotations(cls, conn):
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
            if len(popular) > 1:
                _, pop2 = popular[1]
                if pop1 == pop2:
                    # No consensus, skip
                    continue
            ret[identifier] = label1
        return ret

    def group_and_convert_text_anns(self, conn):
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
            probs_pos = [0.0 for _ in range(max_len)]
            probs_neg = [0.0 for _ in range(max_len)]
            probs_neu = [0.0 for _ in range(max_len)]
            for annotation in annotations[identifier]:
                for i, ann in enumerate(annotation):
                    if ann == "p":
                        probs_pos[i] += 1.0
                    elif ann == "n":
                        probs_neg[i] += 1.0
                    elif ann == "e":
                        probs_neu += 1.0
            # Then normalize so everything's <= 1.0
            probs_pos = [i/len(annotations[identifier]) for i in probs_pos]
            probs_neu = [i/len(annotations[identifier]) for i in probs_neu]
            probs_neg = [i/len(annotations[identifier]) for i in probs_neg]
            ret.append((text, probs_pos, probs_neu, probs_neg, identifier))

        return ret

    def execute(self, path, conn):
        documents = self.group_and_convert_text_anns(conn)
        annotations = self.load_annotations(conn)
        exporter = ARFFExporter(self.path, "word_sub")
        word_indices = {}
        for text, pos, neu, neg, identifier in documents:
            for word in text.split(' '):
                word = self.normaliser.normalise_output_word(word)
                if self.normaliser.is_stop_word(word):
                    word = "STOPPED"
                exporter.add_attribute("%s_pos" % (word,), "numeric")
                exporter.add_attribute("%s_neu" % (word,), "numeric")
                exporter.add_attribute("%s_neg" % (word,), "numeric")
                if word not in word_indices:
                    word_indices[word] = len(word_indices)

        exporter.add_attribute("overall", ["positive", "negative", "neutral"])

        row_buf = []

        for text, pos, neu, neg, identifier in documents:
            row_pos = [0.0 for i in range(len(word_indices))]
            row_neg = [0.0 for i in range(len(word_indices))]
            row_neu = [0.0 for i in range(len(word_indices))]
            for word, p, e, n in zip(text.split(' '), pos, neu, neg):
                word = self.normaliser.normalise_output_word(word)
                if self.normaliser.is_stop_word(word):
                    word = "STOPPED"
                row_pos[word_indices[word]] += p
                row_neg[word_indices[word]] += n
                row_neu[word_indices[word]] += e

            row = list(chain.from_iterable([(i, j, k) for i, j, k in zip(row_pos, row_neu, row_neg)]))
            if identifier not in annotations:
                continue
            row.append(annotations[identifier])
            row_buf.append(row)

        exporter.write(row_buf)

        return True, conn


class SubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    """
        Export word-level subjectivity scores to an ARFF file for exploration.
    """

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute.
        """
        super(SubjectiveARFFExporter, self).__init__(
            xml
        )
        self.path = xml.get("path")
        self.export_presence = xml.get("exportPresence")
        self.export_subjectivity = xml.get("exportSubjectivity")
        if self.export_presence == "true":
            self.export_presence = True
        else:
            self.export_presence = False
        if self.export_subjectivity == "false":
            self.export_subjectivity = False
        else:
            self.export_subjectivity = True
        assert self.path is not None

    def group_and_convert_text_anns(self, conn):
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
                for i, ann in enumerate(annotation):
                    if ann != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            ret.append((text, probs, identifier))

        return ret

    @classmethod
    def load_annotations(cls, conn):
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
            if len(popular) > 1:
                _, pop2 = popular[1]
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
        documents = self.group_and_convert_text_anns(conn)
        words = set([])
        output_buf = {}
        labels = self.load_annotations(conn)
        for text, anns, identifier in documents:
            text = text.split(' ')
            first = True
            word_anns = {}
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
            output_buf[identifier] = word_anns

        # Output the ARFF file
        with open(self.path, 'w') as output_file:
            print >> output_file, "@relation subjective"
            if self.export_subjectivity:
                for word in sorted(words):
                    print >> output_file, "@attribute ", word, " numeric"
            if self.export_presence:
                for word in sorted(words):
                    print >> output_file, "@attribute ", "%s_present" % (word, ), " {1, 0}"
            print >> output_file, "@attribute overall_annotation {positive, negative, neutral}"
            print >> output_file, ""
            print >> output_file, "@data"
            csv_writer = csv.writer(output_file)
            for identifier in output_buf:
                if identifier not in labels:
                    continue # No consensus for this entry
                buf = output_buf[identifier]
                print buf
                row = []
                if self.export_subjectivity:
                    for word in sorted(words):
                        if word in buf:
                            row.append(buf[word])
                        else:
                            row.append(0.0)
                if self.export_presence:
                    for word in sorted(words):
                        if word in buf:
                            row.append(1)
                        else:
                            row.append(0)
                row.append(labels[identifier])
                logging.debug(row)
                csv_writer.writerow(row)

        return True, conn
