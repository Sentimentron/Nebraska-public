#!/usr/bin/env python

"""
    Annotators modify the input table by adding additional columns.
    These columns describe some unique thing about the input document,
    such as its length.
"""

import types
import logging

from sentiwordnet import SentiWordNetReader

from nltk.corpus import wordnet as wn

class Annotator(object):
    """
        Base, abstract annotator class
    """

    def __init__(self, column_name, column_type):
        """
            Construct the base annotator

            Args:
                column_name: What to call the annotation column
                column_type: Accepted values are Types.FloatType
        """

        if column_type == types.FloatType:
            self.column_type = "FLOAT"
        elif column_type == types.IntType:
            self.column_type = "INTEGER"
        else:
            raise TypeError(column_type)

        self.column_name = column_name

    def create_additional_input_column(self, db_conn):
        """
            Create the additional input column required by this annotator.
        """

        logging.info("Creating annotation column...")
        cursor = db_conn.cursor()
        sql = "ALTER TABLE input ADD COLUMN %s %s" % (
            self.column_name, self.column_type
        )
        logging.debug(sql)
        cursor.execute(sql)
        logging.info("Committing changes...")
        db_conn.commit()

    @classmethod
    def get_input_set(cls, db_conn):
        """
            Returns a list of documents suitable for annotation.

            By default, this returns every document.
        """
        annotation_set = set([])
        cursor = db_conn.cursor()
        cursor.execute("SELECT identifier, document FROM input")
        for row in cursor.fetchall():
            annotation_set.add(row)
        return annotation_set

    def execute(self, _, db_conn):
        """
            Produce the annotations using the abstract annotate_doc method
        """

        self.create_additional_input_column(db_conn)

        failed = set([])
        cursor = db_conn.cursor()
        update_sql = "UPDATE input SET %s = ? WHERE identifier = ?" % (
            self.column_name,
        )

        # Read the input documents
        annotation_set = self.get_input_set(db_conn)

        for identifier, text in annotation_set:
            # Annotate each input document
            value = self.produce_annotation(identifier, text, db_conn)
            if value is None:
                failed.add(identifier)
                logging.debug("Annotation failed: %d", identifier)
            # Save the annotation
            cursor.execute(update_sql, (value, identifier))

        if len(failed) != 0:
            logging.info("Failed to annotate %d entries", len(failed))

        logging.info("Committing changes...")
        db_conn.commit()
        return True, db_conn

    def produce_annotation(self, identifier, text, db_conn):
        """
            Abstract stub method
        """
        del identifier, text, db_conn
        raise NotImplementedError()

class DomainSpecificAnnotator(Annotator):

    def __init__(self, domain, column_name, column_type):
        super(DomainSpecificAnnotator, self).__init__(
            column_name, column_type
        )

        self.domain = domain

    def get_input_set(self, db_conn):
        """
            Returns a list of documents suitable for annotation
            (i.e. the ones in the domain)
        """

        cursor = db_conn.cursor()

        # Resolve the domain
        cursor.execute(
            "SELECT label_identifier FROM label_names_domains WHERE label = ?",
            (self.domain, )
        )
        for domain_identifier, in cursor.fetchall():
            pass

        annotation_set = set([])
        cursor = db_conn.cursor()
        cursor.execute("""SELECT identifier, document
            FROM input JOIN label_domains ON document_identifier = identifier
            WHERE label = ?""", (domain_identifier,))
        for row in cursor.fetchall():
            annotation_set.add(row)
        return annotation_set

class FinancialDistanceAnnotator(DomainSpecificAnnotator):
    """
        Annotates tweets with the average distance measure of each synset
        from a set of target synsets.

        Idea is to use POS-tagging as a crude word-sense disambiguation.
    """
    def __init__(self, xml):
        """
            XML should have:

                A set of child Synset elements such as
                    <Synset>bankrupt.v.01</Synset>
                    (other tags are ignored)

                An attribute named "pos" which says where the POS
                tags come from

                    POS tokens must be in the form "pos/token" i.e.
                        V/starred
        """
        super(FinancialDistanceAnnotator, self).__init__(
            "finance", "financial", types.FloatType
        )
        self.synsets = set([])
        for child in xml:
            if child.tag == "Synset":
                self.synsets.add(child.text)
        logging.debug(self.synsets)
        self.synsets = set([wn.synset(i) for i in self.synsets])
        self.pos_name = xml.get("pos")
        self.pos_table = "pos_%s" % (self.pos_name,)
        self.pos_tokens = "pos_tokens_%s" % (self.pos_name, )
        self._tag_database_initialized = False
        self.tag_database = {}

    def initialize_tag_database(self, db_conn):
        """
            Creates the identifier -> token map in memory
        """
        cursor = db_conn.cursor()
        cursor.execute("SELECT identifier, token FROM %s" % (self.pos_tokens,))
        for identifier, token in cursor.fetchall():
            identifier = int(identifier)
            self.tag_database[identifier] = token
        self._tag_database_initialized = True

    def retrieve_tag(self, db_conn, token_identifier):
        """
            Retrieve the token using POS-representation identifier
        """
        if not self._tag_database_initialized:
            self.initialize_tag_database(db_conn)

        return self.tag_database[token_identifier]


    @classmethod
    def filter_tag_based_on_synset(cls, synset, tag):
        """
            Determine if a given candidate tag matches the part of speech of a
            given synset.
        """
        syn_pos = synset.pos
        tag_pos, _, _ = tag.partition('/')
        if syn_pos == tag_pos.lower():
            return True
        return False

    @classmethod
    def compute_distance_measure(cls, source_synset, target_synset):
        """
        Returns the distance measure between a source_synset and
        a target_synset
        """
        return source_synset.path_similarity(target_synset)
        #return source_synset.shortest_path_distance(target_synset)

    @classmethod
    def retrieve_filter_word_synsets(cls, source_synset, tag):
        """Return a set of matching synsets based on POS tags"""
        _, _, word = tag.partition('/')
        synsets = wn.synsets(word)
        return [s for s in synsets if s.pos == source_synset.pos]

    def produce_annotation(self, identifier, text, db_conn):
        cursor = db_conn.cursor()
        # Load the POS tagged tweet
        cursor.execute(
            "SELECT tokenized_form FROM %s WHERE document_identifier = ?" % (
                self.pos_table,
                ), (identifier, )
        )
        tokenized_form = None
        for tokenized_form, in cursor.fetchall():
            pass
        if tokenized_form is None:
            raise ValueError((identifier, text))

        # Split the POS-tagged tweet
        tokenized_form = [i for i in [
            j.strip() for j in tokenized_form.split(' ')]
            if len(i) > 0
        ]

        # Convert into identifiers
        tokenized_identifiers = set([int(i) for i in tokenized_form])
        # Retrieve the POS-tags
        tags = set(
            [self.retrieve_tag(db_conn, i) for i in tokenized_identifiers]
        )
        target_similarities = []
        for target_synset in self.synsets:
            candidate_tags = [
                i for i in tags if self.filter_tag_based_on_synset(
                    target_synset, i
                )
            ]
            if len(candidate_tags) == 0:
                continue
            best = 0
            for tag in candidate_tags:
                for source_synset in self.retrieve_filter_word_synsets(target_synset, tag):
                    distance = self.compute_distance_measure(source_synset, target_synset)
                    if distance is None:
                        continue
                    if distance > best:
                        best = distance

            target_similarities.append(best)
        # Return the total average distance
        distance = None
        if len(target_similarities) > 0:
            logging.debug(target_similarities)
            logging.debug(sum(target_similarities))
            logging.debug(len(target_similarities))
            distance = sum(target_similarities) / len(target_similarities)

        logging.debug((text, distance))
        return distance


class SubjectivityAnnotator(Annotator):
    """
        Annotates tweets with a crude subjectivity score computed
        using SentiWordNet
    """

    def __init__(self, _):
        """
            Constructs the SubjectivityAnnotator, loads SentiWordNet etc.
        """
        super(SubjectivityAnnotator, self).__init__(
            "subjectivity", types.FloatType
        )
        logging.info("Loading SentiWordNet...")
        self.swr = SentiWordNetReader()

    def produce_annotation(self, identifier, text, db_conn):
        """
            Produce an average subjectivity (between 0 and 1) of text
        """
        del identifier, db_conn
        words = [w.lower() for w in text.split(' ')]
        subjectivity = [self.swr.get_subjectivity(w) for w in words]
        average = [s for s in subjectivity if s != None]

        return sum(average)*1.0/max(len(average), 1.0)
