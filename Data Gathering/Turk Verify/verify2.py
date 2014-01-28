#!/usr/bin/env python
from __future__ import division
import csv
import fileinput
import sys
# import Levenshtein
import re

class Verify(object):

    def __init__(self):
        self.SUB_PHRASE = 30
        self.TWEET = 28
        self.WORKER_ID = 15
        self.REJECT = 34
        self.black_list = self.loadBlackList()
        self.minLengthToCheck = 1
        self.masterAnnotations = self.loadMasterAnnotations()
        self.scoreMap = self.loadScoreMap()
        pass

    def loadScoreMap(self):
        #make new hashmap of 2 letter combination
        myMap = {}
        myMap["qq"] = 0
        myMap["qp"] = -1
        myMap["qn"] = -1
        myMap["qe"] = -0.1
        myMap["pq"] = -1
        myMap["pp"] = 0
        myMap["nn"] = 0
        myMap["pn"] = -1
        myMap["pe"] = -0.5
        myMap["nq"] = -0.1
        myMap["np"] = -1
        myMap["ne"] = -0.5
        myMap["eq"] = -1
        myMap["ep"] = -0.5
        myMap["en"] = -0.1
        myMap["ee"] = 0
        return myMap

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

    def arePositiveSubphrasesTheCorrectLength(self, row):
        tweet_length = len(row[self.TWEET])
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
        tweet_length = len(row[self.TWEET])
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
        tweet_length = len(row[self.TWEET])
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

    def setScore(self, row):
        #Method gets one row from turk results and accesses the annotation.
        #It then calculates a score based on our annotation and user's.
        #p&p=0 n&n=0 e&e=0 p&e = -0.5 n&e=-0.5 p&n=-1

        annotation = row[self.SUB_PHRASE]
        ourAnnotation = self.masterAnnotations[row[self.TWEET]]

        if(len(annotation)!=len(ourAnnotation)):
            #add insignificant letters to end of annotation
            annotation = self.padAnnotation(ourAnnotation, annotation)

        #use regex to replace all non key letters to q
        annotation = re.sub("[^p|^n|^e]", "q", annotation)
        ourAnnotation = re.sub("[^p|^n|^e]", "q", ourAnnotation)

        finalScore = 0

        for i in range(0,len(ourAnnotation)-1):
            finalScore = finalScore + self.getScore(annotation[i], ourAnnotation[i])

        return finalScore

    def getScore(self, letter1, letter2):
        return self.scoreMap[letter1+letter2]

    def padAnnotation(self, ourAnnotation, annotation):
        difference = abs(len(ourAnnotation) - len(annotation))

        if(len(ourAnnotation)>len(annotation)):
            for i in range(1,difference):
                annotation=annotation+'q'
        else:
            annotation = annotation[0:len(ourAnnotation)]

        return annotation


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
