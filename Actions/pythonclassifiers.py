#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from sklearn import cross_validation, svm, metrics, tree, neighbors
from sklearn.naive_bayes import GaussianNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

class PythonClassifiers(object):

    def __init__(self, xml):
        self.cls = xml.get("classifier")
        self.classifier = eval(self.cls)
        self.folds = int(xml.get("folds"))
        self.pos_table = xml.get("posSrc")
        self.label_table = xml.get("labelSrc")

    def loadData(self, conn):
        c = conn.cursor()
        sql = "SELECT tokenized_form AS document, label FROM pos_%s NATURAL JOIN label_%s " % (self.pos_table, self.label_table)
        c.execute(sql)
        results = c.fetchall()
        output = []
        for result in results:
            output.append(list(result))
        return output

    def execute(self, path, conn):
        results = self.loadData(conn)
        vectorizer = CountVectorizer(min_df=1, stop_words="english")
        x = []
        y = []
        for document, label in results:
            x.append(document)
            y.append(label)
        x = vectorizer.fit_transform(x)
        y = np.asarray(y)
        scores = cross_validation.cross_val_score(self.classifier, x.todense(), y, cv=self.folds)
        print("------- %s -------- ") % self.cls
        print("Accuracy %s") % scores.mean()
        return True,conn




