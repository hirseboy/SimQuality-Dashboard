# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import csv
import shutil
import sys
import json

import dash.exceptions
import cProfile
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table, exceptions
from dash.dependencies import Input, Output, State

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

def stripVariable(v):
    p = v.find("(mean)")
    if p == -1:
        p = v.find("[")
    if p == -1:
        printError("    Missing unit in header label '{}' of 'Reference.tsv'".format(v))
        return None
    return v[0:p].strip()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.renderer = 'var renderer = new DashRenderer();'
server = app.server

TESTDATA = dict()

try:
    COLORS = readDict("ToolColors.tsv")
except IOError as e:
    print(e)
    print(f"Could not read 'ToolColors.tsv' file.")
    exit(1)

SUBDIRS = sorted(listTestCaseDirectories("test_data"))

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
                    value=SUBDIRS[0]
                ),
                "Choose a Variable:",
                dcc.Dropdown(id="testcase-variant-dropdown"),

                # dcc.Store stores all test case data client side
                dcc.Store(id='testcase-data'),

                # dcc.Store stores all test case data client side
                dcc.Store(id='testcase-variant-data'),
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
                id='evaluation-table',
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
def clean_data(selected_testcase):
    # some expensive data processing step
    try:
        testCaseDescription = readTestCaseDescriptionFile('test_data',  selected_testcase)
    except IOError:
        raise Exception(f"Could not read test case description of test case {selected_testcase}.")

    try:
        variables = readVariables('test_data',  selected_testcase)
    except IOError:
        raise Exception(f"Could not read test case description of test case {selected_testcase}.")

    return [{'label': i, 'value': i} for i in variables], \
           variables[0], \
           testCaseDescription


# Figure is updated
@app.callback(
    Output('testcase-graph', 'figure'),
    Output('evaluation-table', 'data'),
    Input('testcase-variant-dropdown', 'value'),
    State('testcase-dropdown', 'value')
)
def update_testcase_variant_data(testcase_variant, testcase):
    prof = cProfile.Profile()
    prof.enable()
    sys.stdout = open(os.devnull, 'w')
    sqd = analyseTestCase("test_data", testcase, testcase_variant)
    sys.stdout = sys.__stdout__
    prof.disable()
    prof.dump_stats("analyseTestCase.prof")

    resultDf = sqd.caseResultData[testcase_variant]
    evaluationDf = sqd.caseEvaluationResults

    fig = px.line(resultDf, x="Date and Time", y=resultDf.columns[1:], template="simple_white",
                      title=testcase_variant, labels={"y": testcase_variant})
    fig.data[0].update(mode='markers')

    for figline in fig.data:
        figline.line.color = COLORS[figline.name]

    filtedDf = evaluationDf[evaluationDf['Variable'] == testcase_variant].drop(['Variable'], axis=1)

    return fig, filtedDf.to_dict('records')

@app.callback(
    Output("download-testcase-data", "data"),
    Input("btn-testcase-data", "n_clicks"),
    State("testcase-dropdown", "value"),
    prevent_initial_call=True,
)
def func(n_clicks, value):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    # zip all data in data folder
    return dcc.send_file(
        zipTestCaseData(f"./test_data/{value}/data", f"{value}-data")
    )


if __name__ == '__main__':
    app.title = "SimQuality Dashboard"
    app.run_server(debug=True)
