#!/bin/bash

# Installs External/ JARS into a local Maven repository

rm -Rvf ./repo/*
rm -Rvf $HOME/.m2/repository/edu/cmu/cs/ark-tweet-nlp/0.3.2/*

mvn install:install-file -Dfile=../../ark-tweet-nlp-0.3.2.jar -DgroupId=edu.cmu.cs -DartifactId=ark-tweet-nlp -Dversion=0.3.2 -Dpackaging=jar -DlocalRepositoryPath=./repo
