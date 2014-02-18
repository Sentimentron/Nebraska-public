#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

from amt import AMTInputSource
from amt import AMTNormalise
from annotators import FinancialDistanceAnnotator
from annotators import SubjectivityAnnotator
from basic import BasicFilter
from basic import BasicNotFilter
from basic import LineBreakFilter
from db import create_sqlite_connection
from db import create_sqlite_temp_path
from domain import DomainLabeller
from filter import HasLabelFilter
from filter import HasNoLabelFilter
from filter import LabelFilter
from gimpel import GimpelPOSTagger
from metadata import fetch_metadata
from metadata import get_git_version
from metadata import push_metadata
from ml import ClusterLabeller
from ourinput import OurInputSource
from pos import NLTKPOSTagger
from pos import StanfordTagger
from pos import WhiteSpacePOSTagger
from posfilter import POSRewriteFromWhiteList
from posfilter import POSWhiteListUnpopularTags
from posfilter import RewritePOSFilter
from previous import PreviousWorkflow
from results import ResultPivotTableOutput
from sanders import SandersInputSource
from sascha import SaschaInputSource
from semval import SemvalInputSource
from sentiwordnet import SentiWordNetPositiveOrNegativeStrengthLabeller
from sentiwordnet import SentiWordNetPositiveStrengthLabeller
from stemmer import Stemmer
from sub import CRFSubjectiveExporter
from sub import ProduceCRFSTagList
from sub import EmpiricalSubjectivePhraseAnnotator
from sub import FixedSubjectivePhraseAnnotator
from sub import NLTKSubjectivePhraseBayesianAnnotator
from sub import NTLKSubjectivePhraseMarkovAnnotator
from sub import SubjectiveAnnotationEvaluator
from sub import SubjectiveARFFExporter
from sub import SubjectiveCrossValidationEnvironment
from sub import SubjectivePhraseARFFExporter
from sub import SubjectivePhraseTweetClassficationDiscreteARFFExporter
from sub import SubjectivePhraseTweetClassificationARFFExporter
from sub import UnigramBinaryPresenceARFFExporter
from sub import UnigramBinaryPresenceWithPercentageSubjectiveARFFExporter
from templabeller import AtMentionLabeller
from templabeller import BasicWordLabeller
from templabeller import BigramLabeller
from templabeller import EmoticonLabeller
from templabeller import HashTagLabeller
from templabeller import LengthLabeller
from templabeller import ProbablySpamUnicodeLabeller
from templabeller import SpecialCharacterLengthLabeller
from templabeller import TrainingTestSplitLabeller
from twitter import TwitterInputSource
from unique import UniqueFilter
from unique import UniqueTextFilter
from weka import WekaBenchmark
from weka import WekaBenchmarkExport
from weka import WekaClassify
from weka import WekaCrossDomainBenchmark
from weka import WekaResultsExport
from workflow_action_types import WorkflowActionWithOptions

try:
    from pythonclassifiers import PythonClassifiers
except ImportError:
    logging.error("python classifiers aren't available")
