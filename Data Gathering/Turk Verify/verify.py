#!/usr/bin/env python
import csv
import fileinput
import sys

class Verify(object):

    def __init__(self):
        self.SUB_PHRASE = 30
        self.TWEET = 28
        pass

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
            return False, "Subphrases must be annotated"
        else:
            return True, ""

    def writeRow(self, row):
        with open('results2.csv', 'a+b') as csvfile:
            resultswriter = csv.writer(csvfile, delimiter=',')
            resultswriter.writerow(row)




def main():
    file_name = sys.argv[1]
    checker = Verify()
    rows = checker.readInData(file_name)
    APPROVE = 33
    REJECT = 34
    for row in rows:
        good = 1
        result, feedback = checker.isSubphrasePresent(row)
        good = good & result

        if(good):
            row[APPROVE] = "x"
        else:
            row[REJECT] = feedback

        checker.writeRow(row)


if  __name__ =='__main__':
    main()
