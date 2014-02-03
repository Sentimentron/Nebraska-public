#!/usr/bin/env python
from __future__ import division
import csv
import fileinput
import sys
import re

class Verify(object):

    def __init__(self):
        self.SUB_PHRASE = 30
        self.TWEET = 28
        self.WORKER_ID = 15
        self.REJECT = 34
        self.black_list = self.loadBlackList()
        self.minLengthToCheck = 5
        pass

    def loadBlackList(self):
        return set(line.strip() for line in open('blacklist.txt'))

    def readInData(self, filename):
        rows = []
        with open(filename, 'rU') as csvfile:
            turkreader = csv.reader(csvfile, delimiter=",")
            turkreader.next()
            for row in turkreader:
                rows.append(row)
        return rows

    def isSubphrasePresent(self, row):
        if(len(row[self.SUB_PHRASE]) == 0):
            row[self.REJECT] = "Subphrases must be annotated"
            self.writeRow(row)
            return False
        else:
            return True

    def writeRow(self, row):
        with open('results2.csv', 'a+b') as csvfile:
            resultswriter = csv.writer(csvfile, delimiter=',')
            resultswriter.writerow(row)

    def isWorkerAllowed(self, row):
        if(row[self.WORKER_ID] in self.black_list):
            row[self.REJECT] = "You have submitted too many low quality HITS, please do not complete any more HITS for us as your work will be automatically rejected."
            self.writeRow(row)
            return False
        else:
            return True

    def arePositiveSubphrasesTheCorrectLength(self, row):
        tweet_length = len(row[self.TWEET].split())
        subphrase = row[self.SUB_PHRASE]
        number_of_p = subphrase.count("p")
        percent_positive = (number_of_p / tweet_length) *100
        if(percent_positive >6 and tweet_length > self.minLengthToCheck):
            row[self.REJECT] = "Your positive subphrase(s) are too long please read our guidelines to see what we expect and contact us if you are unsure."
            self.writeRow(row)
            return False
        else:
            return True

    def areNegativeSubphrasesTheCorrectLength(self, row):
        tweet_length = len(row[self.TWEET].split())
        subphrase = row[self.SUB_PHRASE]
        number_of_n = subphrase.count("n")
        percent_negative = (number_of_n / tweet_length) *100
        if(percent_negative >20 and tweet_length > self.minLengthToCheck):
            row[self.REJECT] = "Your negative subphrase(s) are too long please read our guidelines to see what we expect and contact us if you are unsure."
            self.writeRow(row)
            return False
        else:
            return True

    def areNeutralSubphrasesTheCorrectLength(self, row):
        tweet_length = len(row[self.TWEET].split())
        subphrase = row[self.SUB_PHRASE]
        number_of_e = subphrase.count("e")
        percent_neutral = (number_of_e / tweet_length) *100
        if(percent_neutral >5 and tweet_length > self.minLengthToCheck):
            row[self.REJECT] = "Your neutral subphrase(s) are too long please read our guidelines to see what we expect and contact us if you are unsure."
            self.writeRow(row)
            return False
        else:
            return True

    def isWholeTweetAnnotated(self, row):
        tweet_length = len(row[self.TWEET].split())
        subphrase = row[self.SUB_PHRASE]
        number_of_e = subphrase.count("e")
        number_of_n = subphrase.count("n")
        number_of_p = subphrase.count("p")
        if(number_of_p >= tweet_length or number_of_n >= tweet_length or number_of_e >= tweet_length):
            row[self.REJECT] = "You have annotated the whole tweet as a subphrase please read our guidelines to ensure you understand what we require and contact us if you are unsure."
            self.writeRow(row)
            return False
        else:
            return True

    def normaliseNonSentimentCharacter(self, row):
        row[self.SUB_PHRASE] = re.sub("[^p|^n|^e]", "q", row[self.SUB_PHRASE])

    def isAnnotationStyleCorrect(self, row):
        # Check they haven't entered phrases here
        pass

    def arePositiveSubphrasesRunsTheCorrectLength(self, row):
        # Check the runs of subphrases are not too long
        pass

    def isSubphraseTooShort(self, row):
        # Need to determine a min % of the tweet that needs to be annotated on average
        pass


def main():
    file_name = sys.argv[1]
    checker = Verify()
    rows = checker.readInData(file_name)
    APPROVE = 33
    for row in rows:
        result =  checker.isSubphrasePresent(row)
        if(not result):
            continue
        result =  checker.isWorkerAllowed(row)
        if(not result):
            continue
        result  = checker.arePositiveSubphrasesTheCorrectLength(row)
        if(not result):
            continue
        result  = checker.areNegativeSubphrasesTheCorrectLength(row)
        if(not result):
            continue
        result  = checker.areNeutralSubphrasesTheCorrectLength(row)
        if(not result):
            continue
        result = checker.isWholeTweetAnnotated(row)
        if(not result):
            continue

        row[APPROVE] = "x"
        checker.writeRow(row)


if  __name__ =='__main__':
    main()
