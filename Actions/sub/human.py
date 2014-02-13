#!/usr/bin/env python

"""
    Defines a base class for subjective phrase annotators
    which rely on human input to work.
"""

import math

from Actions.sub.sub import SubjectivePhraseAnnotator

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
