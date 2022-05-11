# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import os

import dash.exceptions
import pandas as pd
import plotly.express as px
import cProfile
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State

sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from ReadDashData import *

RESULTDIR = "dash_data"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.renderer = 'var renderer = new DashRenderer();'
server = app.server

TESTDATA = dict()
global EVALUATIONDATA
EVALUATIONDATA = pd.read_csv(os.path.join(RESULTDIR, "Results.tsv"), encoding='utf-8', sep="\t",
                             engine="pyarrow").reset_index()
global EVALUATIONDF
EVALUATIONDF = EVALUATIONDATA.copy()

try:
    COLORS = readDict("ToolColors.tsv")
    COLORSTABLE = COLORS.copy()
    COLORSTABLE.pop('Reference', None)
except IOError as e:
    print(e)
    print(f"Could not read 'ToolColors.tsv' file.")
    exit(1)

SUBDIRS = sorted(readTestCaseDirectories(RESULTDIR))

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

            html.H3(
                children='Options',
                style={
                    'textAlign': 'left',
                }
            ),

            html.Div([
                dcc.Checklist(['Show statistical evaluation data'], ['Show statistical evaluation data'],
                              id="statistical-checkstate", inline=True)
            ]),
        ], style={'padding': 10, 'flex': "1 1 20%"}),

        # right dif div
        html.Div([
            dcc.Graph(
                id='testcase-graph',
                style={'height': '600vp'},
            ),

            dash_table.DataTable(
                id='evaluation-table',
                editable=False,
                style_as_list_view=True,
                sort_action='native',
                hidden_columns=["ToolID"],
                style_data_conditional=[
                                             {
                                                 'if': {
                                                     'filter_query': '{{ToolID}} = {}'.format(
                                                         tool),
                                                 },
                                                 'border-bottom': "1px solid" + COLORSTABLE[tool]
                                             } for tool in COLORSTABLE.keys()
                                         ] +
                                         [
                                             {
                                                 'if': {
                                                     'column_id': 'ToolID'
                                                 },
                                                 'textAlign': 'left'
                                             },
                                         ],
                style_header_conditional=[
                                               {
                                                   'if': {
                                                       'column_id': 'ToolID'
                                                   },
                                                   'textAlign': 'left'
                                               },
                                           ],

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
        testCaseDescription = readTestCaseDescriptionFile(RESULTDIR, selected_testcase)
    except IOError:
        raise Exception(f"Could not read test case description of test case {selected_testcase}.")

    try:
        variables = readVariables(RESULTDIR, selected_testcase)
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
    State('testcase-dropdown', 'value'),
    Input('statistical-checkstate', 'value')
)
def update_testcase_variant_data(testcase_variant, testcase, checksate):
    prof = cProfile.Profile()
    prof.enable()

    norms = ['CVRMSE', 'Daily Amplitude CVRMSE', 'MBE', 'RMSEIQR', 'MSE', 'NMBE', 'NRMSE', 'RMSE', 'RMSLE',
             'R squared', 'std dev', 'Maximum', 'Minimum', 'Average']
    try:
        resultDf = readDashData(RESULTDIR, testcase, testcase_variant)
    except Exception as e:
        printError(str(e))
        printError(f"Could not read test case {testcase} and variable {testcase_variant}.")

    # evaluationDf = pd.read_csv(os.path.join(RESULTDIR, "Results.tsv"), encoding='utf-8', sep="\t", engine="pyarrow").reset_index()
    EVALUATIONDF = EVALUATIONDATA.copy()
    if not checksate:
        for norm in norms:
            EVALUATIONDF = EVALUATIONDF.drop([norm], axis=1)

    fig = px.line(resultDf, x="Time", y=resultDf.columns, template="simple_white", title=testcase_variant,
                  labels={"y": testcase_variant})
    fig.data[0].update(mode='markers')

    for figline in fig.data:
        figline.line.color = COLORS[figline.name]
    searchterm = testcase[2:]
    EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Test Case'] == searchterm].drop(['Test Case'], axis=1)
    EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Variable'] == testcase_variant].drop(['Variable'], axis=1)

    def function(x):
        return '⭐⭐⭐' if x == 'Gold' else (
            '⭐⭐' if x == 'Silver' else (
                '⭐' if x == 'Bronze' else '-'
            ))

    EVALUATIONDF['SimQ-Rating'] = EVALUATIONDF['SimQ-Rating'].apply(function)
    prof.disable()
    prof.dump_stats("analyseTestCase.prof")
    return fig, EVALUATIONDF.drop(['index'], axis=1).to_dict('records')

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
