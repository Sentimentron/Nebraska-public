#!/usr/bin/env python
import csv
import fileinput
import sys
import Levenshtein
import re

class Verify(object):

    def __init__(self):
        self.SUB_PHRASE = 30
        self.TWEET = 28
        self.WORKER_ID = 15
        self.REJECT = 34
        self.black_list = self.loadBlackList()
        self.masterAnnotations = self.loadMasterAnnotations()
        pass

    def loadBlackList(self):
        return set(line.strip() for line in open('blacklist.txt'))

    def loadMasterAnnotations(self):
        # Read the master annotations from the CSV and store in a hashmap of tweets -> master annotation
        rows = {}
        with open('masters.csv', 'rU') as csvfile:
            masterreader = csv.reader(csvfile, delimiter=",")
            for row in masterreader:
                rows[row[0]] = row[1]
        return rows

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

    def computeDistanceToMasterAnnotation(self, row):
        # Get the master annotation for this tweet
        master = self.masterAnnotations[row[self.TWEET]]
        turker = row[self.SUB_PHRASE]
        re.sub("[^p|^n|^e]","q", turker)
        ratio = Levenshtein.ratio(master, turker)
        if(ratio < 0.5):
            print(ratio)
            row[self.REJECT] = "Your annotation differs too much from our gold standard annotation, please read our guidelines to ensure you understand what we require"
            return False
        return True


def main():
    file_name = sys.argv[1]
    checker = Verify()
    rows = checker.readInData(file_name)
    APPROVE = 33
    for row in rows:
        good = 1
        result = checker.computeDistanceToMasterAnnotation(row)
        # result =  checker.isSubphrasePresent(row)
        result = result & good
        # result =  checker.isWorkerAllowed(row)
        # result = result & good

        if(good):
            row[APPROVE] = "x"
            checker.writeRow(row)


if  __name__ =='__main__':
    main()
