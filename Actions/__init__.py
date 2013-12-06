#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

from annotators import SubjectivityAnnotator, FinancialDistanceAnnotator

from metadata import fetch_metadata, push_metadata, get_git_version

from basic import BasicFilter, BasicNotFilter, LineBreakFilter
from unique import UniqueFilter, UniqueTextFilter

from twitter import TwitterInputSource
from sanders import SandersInputSource
from sascha import SaschaInputSource
from semval import SemvalInputSource

from templabeller import HashTagLabeller, AtMentionLabeller, BasicWordLabeller, BigramLabeller, LengthLabeller, SpecialCharacterLengthLabeller, ProbablySpamUnicodeLabeller, EmoticonLabeller, TrainingTestSplitLabeller
from ml import ClusterLabeller

from filter import LabelFilter, HasLabelFilter

from db import create_sqlite_temp_path, create_sqlite_connection

from pos import WhiteSpacePOSTagger, NLTKPOSTagger, StanfordTagger
from twitterpos import GimpelPOSTagger

from previous import PreviousWorkflow

from gimpel import GimpelPOSTagger

from weka import WekaBenchmark, WekaClassify, WekaResultsExport, WekaCrossDomainBenchmark, WekaBenchmarkExport
from posfilter import RewritePOSFilter, POSWhiteListUnpopularTags, POSRewriteFromWhiteList

from domain import DomainLabeller

from sentiwordnet import SentiWordNetPositiveOrNegativeStrengthLabeller, SentiWordNetPositiveStrengthLabeller

from ourinput import OurInputSource
try:
    from pythonclassifiers import PythonClassifiers
except ImportError:
    logging.error("python classifiers aren't available")
