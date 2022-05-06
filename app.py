# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Union, Any, Dict

import pandas
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table

import sys
import csv
import shutil

from plotly.graph_objs import Figure

sys.path.append('./scripts')

from ScoreCalculation import *


# Reads a csv file specified by a path and returns a dict with
# all entries from column 1 as keys and all entries from column 2
# as values
# first line is skipped
def readDict(file):
    myDict = dict()
    with open(file, mode='r', encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter='\t')
        next(reader, None)  # skip the headers
        myDict = {rows[0]: rows[1] for rows in reader}

    return myDict


# Download test case data clicked
def zipTestCaseData(dirName, outputFileName):
    return shutil.make_archive(outputFileName, 'zip', dirName)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.renderer = 'var renderer = new DashRenderer();'

TESTDATA = dict()

MEDALS = {0: "Failed", 1: "Gold", 2: "Silver", 3: "Bronze"}

try:
    COLORS = readDict("ToolColors.tsv")
except IOError as e:
    print(e)
    print(f"Could not read 'ToolColors.tsv' file.")
    exit(1)

SUBDIRS = listTestCaseDirectories("test_data")

app.layout = html.Div(
    style={"height": "100vh", 'display': 'flex', 'flex-direction': 'row'},
    children=[
        # left div
        html.Div([

            html.H1(
                children='SimQuality Dashboard',
                style={
                    'textAlign': 'left',
                }
            ),
            html.H3(
                children='Test case selection',
                style={
                    'textAlign': 'left',
                }
            ),

            html.Div([
                "Choose a Test Case:",
                dcc.Dropdown(
                    options=[{'label': str(i).replace("-", " "), 'value': i} for i in SUBDIRS],
                    id="testcase-dropdown",
                    value=SUBDIRS[0]),
                "Choose a Variable:",
                dcc.Dropdown(id="testcase-variant-dropdown"),

            ]),

            html.Div([
                html.H3(
                    children='Test case description',
                    style={
                        'textAlign': 'left',
                    }
                ),
                dcc.Textarea(
                    id='textarea-testcase-description',
                    value='Textarea content initialized\nwith multiple lines of text',
                    style={'width': '100%', 'height': 300},
                ),

            ]),

            html.Div([
                html.H3(
                    children='Download data',
                    style={
                        'textAlign': 'left',
                    }
                ),
                html.Div([
                    html.Div([
                        "Download Test Case",
                    ], style={'verticalAlign': 'middle', 'width': '300px', 'display': 'inline-block'}),
                    html.Div([
                        html.Button('Download', id='btn-testcase-data', n_clicks=0),
                        dcc.Download(id="download-testcase-data")
                    ], style={'verticalAlign': 'middle', 'display': 'inline'}),
                ]),
            ]),
        ], style={'padding': 10, 'flex': "1 1 20%"}),

        # right dif div
        html.Div([
            dcc.Graph(
                id='testcase-graph',
                style={'height': 600},
            ),

            dash_table.DataTable(
                id='evaluation-datatable',
                editable=False
            )
        ], style={'padding': 10, 'flex': "1 1 80%", "height": "100vh"}),
    ])


# Dropdown menu to choose variable is updated

@app.callback(
    Output('testcase-variant-dropdown', 'options'),
    Output('testcase-variant-dropdown', 'value'),
    Output('textarea-testcase-description', 'value'),
    Input('testcase-dropdown', 'value')
)
def update_var_dropdown(selected_testcase):
    # Holds data for currently selected test case
    global TESTDATA
    TESTDATA = analyseTestCase("test_data", selected_testcase)
    return [{'label': i, 'value': i} for i in TESTDATA.caseResultData.keys()], \
           list(TESTDATA.caseResultData.keys())[0], \
           TESTDATA.testCaseDescription


# Figure is updated

@app.callback(
    Output('testcase-graph', 'figure'),
    Output('evaluation-datatable', 'data'),
    Input('testcase-dropdown', 'value'),
    Input('testcase-variant-dropdown', 'value')
)
def update_data(selected_testcase, selected_variant):
    resultDf = TESTDATA.caseResultData[selected_variant]
    fig = px.line(resultDf, x="Date and Time", y=resultDf.columns[1:], template="simple_white")
    fig.data[0].update(mode='markers')

    for figline in fig.data:
        figline.line.color = COLORS[figline.name]

    evaluationDf = pandas.DataFrame()
    evaluationData = TESTDATA.caseEvaluationResults[selected_variant]

    tempDict = dict()

    cols = ['Tools', 'Fehlercode', 'Max', 'Min', 'Average', 'CVRMSE', 'Daily Amplitude CVRMSE', 'MBE', 'RMSEIQR', 'MSE',
            'NMBE', 'NRMSE', 'RMSE', 'RMSLE', 'R squared coeff determination', 'std dev', 'SimQuality-Score',
            'SimQ-Einordnung']

    for col in cols:
        tempDict[col] = []

    for data in evaluationData:
        tempData = evaluationData[data]

        # first we add all the norms
        for norm in tempData.norms:
            if norm not in tempDict.keys():
                continue
            tempDict[norm].append(tempData.norms[norm])

        tempDict["Tools"].append(tempData.ToolID)
        tempDict["SimQuality-Score"].append(tempData.score)
        tempDict["SimQ-Einordnung"].append(MEDALS[tempData.simQbadge])

    for col in tempDict.keys():
        if not tempDict[col]:
            continue
        evaluationDf[col] = tempDict[col]

    return fig, evaluationDf.to_dict('records')


@app.callback(
    Output("download-testcase-data", "data"),
    Input("btn-testcase-data", "n_clicks"),
    Input("testcase-dropdown", "value"),
    prevent_initial_call=True,
)
def func(n_clicks, value):
    # zip all data in data folder
    return dcc.send_file(
        zipTestCaseData(f"./test_data/{value}/data", f"{value}-data.zip")
    )


if __name__ == '__main__':
    app.run_server(debug=True)
