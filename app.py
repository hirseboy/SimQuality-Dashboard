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
import json

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
server = app.server

TESTDATA = dict()

MEDALS = {0: "Failed", 1: "Gold", 2: "Silver", 3: "Bronze"}

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

                # dcc.Store stores the intermediate value
                dcc.Store(id='testcase-result-value'),
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
    Output('testcase-result-value', 'data'),
    Output('testcase-variant-dropdown', 'options'),
    Output('testcase-variant-dropdown', 'value'),
    Output('textarea-testcase-description', 'value'),
    Input('testcase-dropdown', 'value')
)
def clean_data(selected_testcase):
    # some expensive data processing step
    sqd = analyseTestCase("test_data", selected_testcase)

    datasets = {key: sqd.caseResultData[key].to_json(orient='split', date_format='iso') for key in sqd.caseResultData.keys()}

    datasets['Evaluation'] = sqd.caseEvaluationResults.to_json(orient='split', date_format='iso')

    return json.dumps(datasets), \
           [{'label': i, 'value': i} for i in sqd.caseResultData.keys()], \
           list(sqd.caseResultData.keys())[0], \
           sqd.testCaseDescription


# Figure is updated
@app.callback(
    Output('testcase-graph', 'figure'),
    Input('testcase-result-value', 'data'),
    Input('testcase-dropdown', 'value'),
    Input('testcase-variant-dropdown', 'value'),
)
def update_figure(jsonified_cleaned_data, selected_testcase, selected_variant):
    if selected_variant is None:
        return

    datasets = json.loads(jsonified_cleaned_data)
    resultDf = pd.read_json(datasets[selected_variant], orient='split')

    fig = px.line(resultDf, x="Date and Time", y=resultDf.columns[1:], template="simple_white")
    fig.data[0].update(mode='markers')

    for figline in fig.data:
        figline.line.color = COLORS[figline.name]

    return fig


@app.callback(
    Output('evaluation-table', 'data'),
    Input('testcase-result-value', 'data'),
    Input('testcase-variant-dropdown', 'value'),
)
def update_table(jsonified_cleaned_data, selected_testcase):
    if selected_testcase is None:
        return None

    datasets = json.loads(jsonified_cleaned_data)
    df = pd.read_json(datasets['Evaluation'], orient='split')
    filtedDf = df[df['Variable'] == selected_testcase].drop(['0', 'Variable'], axis=1)

    return filtedDf.to_dict('records')


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
