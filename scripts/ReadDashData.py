#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file contains functions to create panda data frames from the "dash data" folder.

import os
import csv
import pandas as pd
import datetime as dt
import pyarrow
import shutil

from PrintFuncs import *


def readVariables(testCaseDir, testCaseName):
    path = os.path.join(testCaseDir, testCaseName)
    dirs = os.listdir(path)

    cleanedDirs = []
    for dir in dirs:
        if dir.endswith('.txt'):
            continue
        if dir.endswith('.tsv'):
            continue
        if dir.endswith('.png'):
            continue
        if dir == "download_data":
            continue
        cleanedDirs.append(dir)
    return sorted(cleanedDirs)

def readTestCaseDirectories(path):
    dirs = []
    # process all subdirectories of `AP4` (i.e. test cases)
    subdirs = os.listdir(path)

    # process all subdirectory starting with TF
    for sd in subdirs:
        if len(sd) > 4 and sd.startswith("TF"):
            if sd.endswith(".txt") or sd.endswith(".txt"):
                continue
            if sd == "download_data":
                continue

            # extract next two digits and try to convert to a number
            try:
                testCaseNumber = int(sd[2:3])
            except Exception:
                printError("Malformed directory name: {}".format(sd))
                continue
            dirs.append(sd.strip())
    return dirs

def readTestCaseDescriptionFile(testCaseDir, testCaseName):
    path = os.path.join(testCaseDir, testCaseName, "TestCaseDescription.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.read().replace("\n", "")

    return str(lines)

def readCommentFile(testCaseDir, testCaseName):
    path = os.path.join(testCaseDir, testCaseName, "Comment.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.read()

    return str(lines)

def readDashboardInformation():
    path = os.path.join(os.getcwd(), "DashboardInformation.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.read()

    return str(lines)

# Reads a csv file specified by a path and returns a dict with
# all entries from column 1 as keys and all entries from column 2
# as values
# first line is skipped
def readDict(file, skipHeader = True):
    myDict = dict()
    with open(file, mode='r', encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter='\t')
        if skipHeader:
          next(reader, None)  # skip the headers
        myDict = {rows[0]: rows[1] for rows in reader}

    return myDict


# Download test case data clicked
def zipTestCaseData(dirName, outputFileName):
    return shutil.make_archive(outputFileName, 'zip', dirName)

def convertToRatingPanda(evaluationDf, testcase):
    ratingDf = pd.DataFrame()

    # first we take only variables containing to the test case
    searchterm = testcase[2:]
    tempDf = evaluationDf.loc[evaluationDf['Test Case'] == searchterm].drop(['Test Case'], axis=1)

    convertDict = dict()
    for index, row in tempDf.iterrows():
        if row["Variable"] not in convertDict.keys():
            convertDict[row["Variable"]] = dict()

        convertDict[row["Variable"]][f"{row['Tool Name']} ({row['Version']})"] = row["SimQ-Rating"]

    ratingDf = pd.DataFrame.from_dict(convertDict, orient='index').reset_index()

    def function(x):
        return '🟩' if x == 'Gold' else (
            '🟨' if x == 'Silver' else (
                '🟨' if x == 'Bronze' else '🟥'
            ))

    for col in ratingDf.columns:
        if col == "index":
            continue
        ratingDf[col] = ratingDf[col].apply(function)

    ratingDf.rename(columns={"index": "Variable"}, inplace=True)

    return ratingDf

def stripVariable(v):
    p = v.find("(mean)")
    if p == -1:
        p = v.find("[")
    if p == -1:
        printError("    Missing unit in header label '{}' of 'Reference.tsv'".format(v))
        return None
    return v[0:p].strip()

def readDashData(resultdir, testcase, testcase_variant):

    path = os.path.join(resultdir, testcase, testcase_variant)
    print(f"Reading test case data in path '{path}")

    testfiles = os.listdir(path)
    print(f"For this test case we found following files:")
    for file in testfiles:
        print(f"{file}")

    # Construct two pandas dataframes
    resultDf = pd.DataFrame()
    timeDf = pd.DataFrame()

    # eg. 'NANDRAD.tsv --> strip the name till "." --> "NANDRAD"
    for file in testfiles:
        toolfile = os.path.join(path, file)
        df = pd.read_feather(toolfile)
        df = df.set_index('index')
        tool = file.split(".")[0] # tool name
        print(f"Reading the tool data file '{toolfile}' and take its name '{tool}'.")

        if tool == 'NANDRAD':
            print(f"Setting the tool with name '{tool}' as time column.")
            timeDf = df

        data = df['Data'].tolist()
        df.columns = [tool]
        resultDf[tool] = df[tool]
        print(f"Result data of tool '{tool}' has been added.")

    index = resultDf.index
    time = []
    for i in resultDf.index:
        time.append(dt.datetime(2020, 1, 1) + dt.timedelta(hours=i))

    print(f"Time Column will be set.")
    resultDf['Time'] = time

    # resort 'reference' to front
    cols = list(resultDf)
    cols.insert(0, cols.pop(cols.index('Reference')))
    resultDf = resultDf.loc[:, cols]

    for col in resultDf.columns:
        if col == "Reference" or col == "Time":
            continue
        resultDf[col].interpolate(inplace=True)

    return resultDf
