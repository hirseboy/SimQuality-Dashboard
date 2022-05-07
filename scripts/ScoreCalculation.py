#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Script to automatically process all simquality test result directories
# and generate a score file.
#
# Script is expected to be run from within the 'data' directory.

import os
import sys

import pandas
import pandas as pd
import plotly.graph_objects as go
from typing import Dict

from PrintFuncs import *
from ProcessDirectory import processDirectory, CaseResults
from TSVContainer import TSVContainer
from dataclasses import dataclass

BADGES = {
    0: "Failed",
    1: "Gold",
    2: "Silver",
    3: "Bronze"
}

@dataclass
class SimQualityData:
    name: str
    testCaseDescription: str

    caseEvaluationResults: []
    caseResultData: Dict

def readWeightFactors():
    # read weight factors
    # CVRMSE	Daily Amplitude CVRMSE	MBE	RMSEIQR	MSE	NMBE	NRMSE	RMSE	RMSLE	R² coefficient determination	std dev
    try:
        weightFactorsTSV = TSVContainer()
        weightFactorsTSV.readAsStrings(os.path.join(os.getcwd(), "WeightFactors.tsv"))
    except RuntimeError as e:
        print(e)
        print(f"At least one weight factor has to be specified in 'WeightFactors.tsv'.")
        exit(1)

    weightFactors = dict()

    for i in range(len(weightFactorsTSV.data[0])):
        weightFactors[weightFactorsTSV.data[0][i]] = int(weightFactorsTSV.data[1][i])

    weightFactors['Sum'] = sum(map(int, weightFactorsTSV.data[1]))  # convert to int and then sum it up

    return weightFactors

def listTestCaseDirectories(path):
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


def readDescriptionFile(filePath):
    with open(filePath, encoding="utf-8") as f:
        lines = f.read().replace("\n", "")

    return str(lines)


def analyseTestCase(path, testCase) -> dict:
    # initialize colored console output
    init()

    weightFactors = readWeightFactors()
    sqd = SimQualityData(testCase, "", dict(), dict())

    # process all subdirectories of `AP4` (i.e. test cases)
    subdirs = os.listdir(path)

    if testCase not in subdirs:
        raise Exception(f"No TestCase Results Folder {testCase} does exist.")

    if 4 < len(testCase) and testCase.startswith("TF"):
        # extract next two digits and try to convert to a number
        try:
            testCaseNumber = int(testCase[2:3])
        except:
            raise Exception("Malformed test case name: {}".format(testCase))

    printNotification("\n################################################\n")
    printNotification("Processing directory '{}'".format(testCase))

    sqd.caseEvaluationResults = processDirectory(os.path.join(path, testCase), weightFactors)

    try:
        sqd.testCaseDescription = readDescriptionFile(os.path.join(path, testCase, "TestCaseDescription.txt"))
    except IOError:
        raise Exception(f"Could not read test case description of test case {testCase}.")

    # we also want to create some plotly charts
    # there fore we create a new data frame
    cer = sqd.caseEvaluationResults
    crd = sqd.caseResultData

    # skip test cases with missing/invalid 'Reference.tsv'
    if cer is None:
        raise Exception("No Test Case Data.")
    for variable in cer:
        for tool in cer[variable]:
            if variable not in crd.keys():
                printNotification(f"Create new data frame.")
                crd[variable] = cer[variable][tool].timeDf
                # add reference results in first round
                crd[variable]['Reference'] = cer[variable][tool].referenceDf.loc[:, 'Data']
                cer[variable][tool].referenceDf = pd.DataFrame(None) # clear data frame
                cer[variable][tool].timeDf = pd.DataFrame(None)  # clear data frame

            crd[variable][cer[variable][tool].ToolID] = cer[variable][tool].toolDataDf.loc[:, 'Data']
            cer[variable][tool].toolDataDf = pd.DataFrame(None)  # clear data frame

    printNotification("\n################################################\n")
    printNotification("Done.")

    return sqd


# ---*** main ***---
if __name__ == "__main__":
    # testCaseDataDfs = scoreCalculation("./test_data", True)
    exit(0)
