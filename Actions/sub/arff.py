#!/usr/bin/env python

"""
    Contains classes for working with WEKA IO for exploration.
"""
import re
import csv
import logging

from collections import defaultdict, Counter

from Actions.sub.human import HumanBasedSubjectivePhraseAnnotator

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
