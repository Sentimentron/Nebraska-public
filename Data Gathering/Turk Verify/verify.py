#!/usr/bin/env python
import csv
import fileinput
import sys

class Verify(object):

    def __init__(self):
        self.SUB_PHRASE = 30
        self.TWEET = 28
        self.WORKER_ID = 15
        self.REJECT = 34
        self.black_list = self.loadBlackList()
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
            return False
        else:
            return True




def main():
    file_name = sys.argv[1]
    checker = Verify()
    rows = checker.readInData(file_name)
    APPROVE = 33
    for row in rows:
        good = 1
        result =  checker.isSubphrasePresent(row)
        result = result & good
        result =  checker.isWorkerAllowed(row)
        result = result & good

        if(good):
            row[APPROVE] = "x"
            checker.writeRow(row)


if  __name__ =='__main__':
    main()
