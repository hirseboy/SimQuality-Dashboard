#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file contains functions to create panda data frames from the "dash data" folder.

import os
import csv
import pandas as pd
import datetime as dt
import pyarrow

from PrintFuncs import *


def readVariables(testCaseDir, testCaseName):
    path = os.path.join(testCaseDir, testCaseName)
    dirs = os.listdir(path)
    for file in dirs:
        if file.endswith(".txt"):
            dirs.remove(file)
    return dirs

def readTestCaseDirectories(path):
    dirs = []
    # process all subdirectories of `AP4` (i.e. test cases)
    subdirs = os.listdir(path)

    # process all subdirectory starting with TF
    for sd in subdirs:
        if len(sd) > 4 and sd.startswith("TF"):
            # extract next two digits and try to convert to a number
            try:
                testCaseNumber = int(sd[2:3])
            except Exception:
                printError("Malformed directory name: {}".format(sd))
                continue
            dirs.append(sd)
    return dirs

def readTestCaseDescriptionFile(testCaseDir, testCaseName):
    path = os.path.join(testCaseDir, testCaseName, "TestCaseDescription.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.read().replace("\n", "")

    return str(lines)

def readDashData(resultdir, testcase, testcase_variant):
    path = os.path.join(resultdir, testcase, testcase_variant)
    testfiles = os.listdir(path)

    resultDf = pd.DataFrame()

    # eg. 'NANDRAD.tsv --> strip the name till "." --> "NANDRAD"
    for file in testfiles:
        toolfile = os.path.join(path, file)
        df = pd.read_feather(toolfile)
        df = df.set_index('index')

        tool = file.split(".")[0] # tool name
        data = df['Data'].tolist()
        df.columns = [tool]
        resultDf[tool] = df[tool]

    index = resultDf.index
    startDate = dt.datetime(2020, 1, 1) + dt.timedelta(hours=index[0])
    resultDf['Time'] = pd.date_range(start=startDate, periods=len(data), freq="H")

    # resort 'reference' to front
    cols = list(resultDf)
    cols.insert(0, cols.pop(cols.index('Reference')))
    resultDf = resultDf.loc[:, cols]

    return resultDf