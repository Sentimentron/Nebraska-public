#!/usr/bin/env python

"""
    Contains classes for working with WEKA IO for exploration.
"""

from human import HuamnBasedSubjectivePhraseAnnotator

class SubjectiveARFFExporter(HumanBasedSubjectivePhraseAnnotator):

    """
        Export word-level subjectivity scores to an ARFF file for exploration.
    """

    def __init__(self, xml):
        """
            Initialise the exporter: must provide a path attribute.
        """
        super(HumanBasedSubjectivePhraseAnnotator, self).__init__(
            xml
        )
        self.path = xml.get("path")
        assert self.path is not None 

    def group_and_convert_text_anns(self, conn, discretise=True):
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
                for i, a in enumerate(annotation):
                    if a != 'q':
                        # If this is part of a subjective phrase,
                        # increment count at this position
                        probs[i] += 1.0
            # Then normalize so everything's <= 1.0
            probs = [i/len(annotations[identifier]) for i in probs]
            if discretise:
                probs = [self.convert_annotation(i) for i in probs]
            ret.append((text, probs, identifier))

        return ret

    def load_annotations(self, conn):
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
            label2, pop2 = popular[1]
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
        documents = self.group_and_convert_text_anns(conn, discretise=False)
        words = set([])
        output_buf = {}
        labels = self.load_annotations(conn)
        for text, anns, identifier in documents:
            text = text.split(' ')
            first = True
            word_anns = defaultdict(float)
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
            output_buf[identifier] = anns

        # Output the ARFF file
        with open(self.path, 'w') as output_file:
            print "@relation subjective" >> output_file
            for word in sorted(words):
                print "@attribute ", word, " numeric" >> output_file 
            print "@attribute overall_annotation {positive, negative, neutral}" >> output_file
            print "" >> output_file
            csv_writer = csv.writer(output_file)
            for identifier in output_buf:
                if identifier not in labels:
                    continue # No consensus for this entry
                csv_writer.writerow([buf[word] for word in sorted(words)] ++ [labels[identifier]])
            csv_writer.close()