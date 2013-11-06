#!/usr/bin/env python

import string
import logging
import re

class TemporaryLabeller(object):

    # TemporaryLabellers operate on disposable tables,
    # label -> identifier mapping typically not retained
    def __init__(self, xml):
        self.dest = xml.get("dest")
        if self.dest is None:
            raise ValueError()
        self.prefix_table = "temporary_label_%s" % (self.dest,)

    def estimate_label_count(self, cursor):
        logging.debug("Getting label count...")
        sql = "SELECT MAX(label) FROM %s" % (self.prefix_table, )
        cursor.execute(sql)
        for count, in cursor.fetchall():
            pass
        logging.debug("%d items found in the table.", count)
        return count + 1


class LiteralLabeller(TemporaryLabeller):

    def execute(self, path, conn):
        # Grab a cursor
        c = conn.cursor()

        logging.info("Labelling documents...")
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        sql = "INSERT INTO %s (document_identifier, label) VALUES (?, ?)" % (self.prefix_table, )
        for identifier, document in c.fetchall():
            # Split method spits out the parts we want to enumerate
            label_id = self.label(document)
            c.execute(sql, (identifier, label_id))

        # Commit changes
        logging.info("Committing changes...")
        conn.commit()
        return True, conn

class EnumeratingLabeller(TemporaryLabeller):

    def execute(self, path, conn):
        # Set up prefix etc
        enumeration = {}

        # Grab a cursor
        c = conn.cursor()

        # Check to see how many items are in the table already
        count = self.estimate_label_count(c)

        # Grab each document
        logging.info("Labelling documents...")
        sql = "SELECT identifier, document FROM input"
        c.execute(sql)
        sql = "INSERT INTO %s (document_identifier, label) VALUES (?, ?)" % (self.prefix_table, )
        for identifier, document in c.fetchall():
            # Split method spits out the parts we want to enumerate
            for token in set(self.split(document)):
                if token not in enumeration:
                    enumeration[token] = count
                    count += 1
                label_id = enumeration[token]
                c.execute(sql, (identifier, label_id))

        # Commit changes
        logging.info("Committing changes...")
        conn.commit()
        return True, conn

class HashTagLabeller(EnumeratingLabeller):

    def split(self, document):
        # Split the document based on spaces
        tokens = document.split(' ')
        tokens = [t for t in tokens if len(t) > 0]
        # Only return those tokens which begin with a hashtag
        return filter(lambda x: x[0] == '#', tokens)

class AtMentionLabeller(EnumeratingLabeller):

    def split(self, document):
        # Again, just on spaces
        tokens = document.split(' ')
        tokens = [t for t in tokens if len(t) > 0]
        # Only return those tokens which begin with an @
        return filter(lambda x: x[0] == '@', tokens)

class BasicWordLabeller(EnumeratingLabeller):

    def only_letters(self, word):
        for w in word:
            if w >= 'a' and w <= 'z':
                continue
            if w >= 'A' and w <= 'Z':
                continue
            return False
        return True

    def split(self, document):
        tokens = document.split(' ')
        tokens = [t for t in tokens if self.only_letters(t) and len(t) >= 5]
        return tokens

class BigramLabeller(EnumeratingLabeller):

    def splittable(self, w):
        if w >= 'a' and w <= 'z':
            return False
        if w >= 'A' and w <= 'Z':
            return False
        if w >= '0' and w <= '9':
            return False
        return True

    def split(self, document):
        tokens = []
        for i in document:
            if not self.splittable(i):
                tokens.append(i)
            else:
                tokens.append(' ')
        tokens = ''.join(tokens).split(' ')
        tokens = [t for t in tokens if len(t) > 4]
        return [(u,v) for u, v in zip(tokens[0:-1], tokens[1:])]

class LengthLabeller(LiteralLabeller):

    def __init__(self, xml):
        super(LengthLabeller, self).__init__(xml)
        self.bin_size = int(xml.get("binSize"))
        assert self.bin_size != None

    def compute_binned_length(self, length):
        return int((length - self.bin_size/2) * 1.0 / self.bin_size) * self.bin_size

    def label(self, document):
        return self.compute_binned_length(len(document))

class SpecialCharacterLengthLabeller(LengthLabeller):

    def label(self, document):
        length = 0
        allowed_set = set(string.uppercase + string.lowercase + ' ')
        for i in document:
            if i not in allowed_set:
                length += 1
        return self.compute_binned_length(length)

class ProbablySpamUnicodeLabeller(LiteralLabeller):

    def compute_unicode_len(self, document):
        length = 0
        allowed_set = allowed_set = set(string.uppercase + string.lowercase + ' ')
        for i in document:
            if i not in allowed_set:
                length += 1
        return length

    def label(self, document):
        if len(document) > 140:
            return 1

        special_len = self.compute_unicode_len(document)
        if special_len > 2 + 12.0/140 * len(document):
            return 1
        else:
            return 0

class EmoticonLabeller(LiteralLabeller):

    def __init__(self, xml):
        super(EmoticonLabeller, self).__init__(xml)
        self.good = [":)", ";)", ":-)", ";-)", ":D", ":-D"]
        self.bad = [":(", ":-(", "D:"]

    def label(self, document):
        good, bad = False, False 
        for goodterm in self.good:
            if goodterm in document:
                good = True 
                break  
        for badterm in self.bad:
            if badterm in document:
                bad = True 
                break 

        if good and bad:
            # Mixed emoticons cant tell return the answer to everything
            return 42
        if good:
            return 1
        if bad:
            return -1
        # No empticons present 
        return 6