# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import os

import dash.exceptions
import pandas as pd
import plotly.express as px
import cProfile
from dash import Dash, dcc, dash_table, html
from dash.dependencies import Input, Output, State

sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from ReadDashData import *

RESULTDIR = "dash_data"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
external_stylesheets = [app.get_asset_url('style.css')]

app.renderer = 'var renderer = new DashRenderer();'
server = app.server

TOOLCOLORS = dict()

TESTDATA = dict()
global EVALUATIONDATA
EVALUATIONDATA = pd.DataFrame()

global EVALUATIONDF
EVALUATIONDF = EVALUATIONDATA.copy()

SUBDIRS = sorted(readTestCaseDirectories(RESULTDIR))

try:
    TOOLCOLORS = readDict(os.path.join(RESULTDIR, "ToolColors.tsv"), False)
    TOOLCOLORS['Reference'] = "#000000"
except IOError as e:
    print(e)
    print(f"Could not read 'ToolColors.tsv' file.")
    exit(1)

app.layout = html.Div(
    style={'display': 'flex', 'flex-direction': 'row'},
    children=[
        # left div
        html.Div([
            html.Img(src=app.get_asset_url('simquality_logo.jpg'),
                     style={'width': '400px'}),
            html.H1(
                children='Dashboard',
                style={
                    'textAlign': 'left',
                }
            ),

            html.Div([

                html.H3(
                    children='Testfall',
                    style={
                        'textAlign': 'left',
                    }
                ),
                dcc.Dropdown(
                    options=[{'label': str(i).replace("-", " "), 'value': i} for i in SUBDIRS],
                    id="testcase-dropdown",
                    value=SUBDIRS[0]
                ),
            ]),

            html.Div([
                html.H3(
                    children='Beschreibung',
                    style={
                        'textAlign': 'left',
                    }
                ),
                dcc.Textarea(
                    id='textarea-testcase-description',
                    disabled=True,
                    value='Textarea content initialized\nwith multiple lines of text',
                    style={'width': '100%', 'height': 300},
                ),

            ]),

            html.Div([

                html.Div([
                    html.Div([
                        html.Button('Download Aufgabenstellung inkl. Daten', id='btn-testcase-data', n_clicks=0),
                        dcc.Download(id="download-testcase-data")
                    ], style={'verticalAlign': 'middle', 'display': 'inline'}),
                ]),
            ]),

            html.H3(
                children='Optionen',
                style={
                    'textAlign': 'left',
                }
            ),

            html.Div([
                dcc.Checklist(['Zeige statistische Kenngrößen'], [],
                              id="statistical-checkstate", inline=True)
            ]),
        ], style={'padding': 10, 'flex': "1 1 20%"}),

        # right dif div
        html.Div([

            dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
                dcc.Tab(label='Variablenanalyse', value='tab-1-example-graph', children=[

                    "Variable:",
                    dcc.Dropdown(id="testcase-variant-dropdown"),

                    dcc.Graph(
                        id='testcase-graph',
                        responsive=True,
                        style={'height': '60vh'}
                    ),

                    dash_table.DataTable(
                        id='evaluation-table',
                        editable=False,
                        style_as_list_view=True,
                        sort_action='native',
                        hidden_columns=["ToolID", "Unit"],
                        css=[{"selector": ".show-hide", "rule": "display: none"}],
                        style_data_conditional=[
                                                   {
                                                       'if': {
                                                           'filter_query': '{{ToolID}} = {}'.format(
                                                               tool),
                                                       },
                                                       'border-bottom': "1px solid" + TOOLCOLORS[tool]
                                                   } for tool in TOOLCOLORS.keys()
                                               ] +
                                               [
                                                   {
                                                       'if': {
                                                           'column_id': 'Tool Name'
                                                       },
                                                       'textAlign': 'left'
                                                   },
                                                   {
                                                       'if': {
                                                           'column_id': 'Editor'
                                                       },
                                                       'textAlign': 'left'
                                                   },
                                                   {
                                                       'if': {
                                                           'column_id': 'Version'
                                                       },
                                                       'textAlign': 'left'
                                                   },
                                               ],
                        style_header_conditional=[
                            {
                                'if': {
                                    'column_id': 'Tool Name'
                                },
                                'textAlign': 'left'
                            },
                            {
                                'if': {
                                    'column_id': 'Editor'
                                },
                                'textAlign': 'left'
                            },
                            {
                                'if': {
                                    'column_id': 'Version'
                                },
                                'textAlign': 'left'
                            },
                        ],

                    )

                ]),
                dcc.Tab(label='Gesamtbewertung', value='tab-2-example-graph', children=[

                    dash_table.DataTable(
                        id='rating-table',
                        editable=False,
                        style_as_list_view=True,
                        sort_action='native',
                        style_data_conditional= [
                                                   {
                                                       'if': {
                                                           'column_id': '{{ToolID}} = {}'.format(
                                                               tool),
                                                       },
                                                       'border-bottom': "1px solid" + TOOLCOLORS[tool]
                                                   } for tool in TOOLCOLORS.keys()
                                                ] +
                                                [
                                                   {
                                                       'if': {
                                                           'column_id': 'Variable'
                                                       },
                                                       'textAlign': 'left'
                                                   },
                                               ],
                        style_header_conditional=[
                            {
                                'if': {
                                    'column_id': 'Variable'
                                },
                                'textAlign': 'left'
                            },
                        ],
                    )

                ]),
            ]),


        ], style={'padding': 10, 'flex': "1 1 80%"}),

        dcc.Loading(
            id="loading-data",
            type="default",
            fullscreen=True
        ),

    ])


# Dropdown menu to choose variable is updated
@app.callback(
    Output('testcase-variant-dropdown', 'options'),
    Output('testcase-variant-dropdown', 'value'),
    Output('textarea-testcase-description', 'value'),
    Output('rating-table', 'data'),
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

    global EVALUATIONDATA
    if EVALUATIONDATA.empty:
        EVALUATIONDATA = pd.read_csv(os.path.join(RESULTDIR, "Results.tsv"), encoding='utf-8', sep="\t", engine="pyarrow").reset_index()

    ratingDf = convertToRatingPanda(EVALUATIONDATA, selected_testcase)

    return [{'label': i, 'value': i} for i in variables], \
           variables[0], testCaseDescription, ratingDf.to_dict('records')


# Figure is updated
@app.callback(
    Output('testcase-graph', 'figure'),
    Output('evaluation-table', 'data'),
    Output('loading-data', 'children'),
    Input('testcase-variant-dropdown', 'value'),
    State('testcase-dropdown', 'value'),
    Input('statistical-checkstate', 'value')
)
def update_testcase_variant_data(testcase_variant, testcase, checksate):
    norms = ['CVRMSE [%]','Daily Amplitude CVRMSE [%]','MBE','RMSEIQR [%]','MSE [%]','NMBE [%]','Average [-]',
             'NRMSE [%]','RMSE [%]','RMSLE [%]','R squared [-]','std dev [-]','Maximum [-]','Minimum [-]','Fehlercode']
    try:
        resultDf = readDashData(RESULTDIR, testcase, testcase_variant)
    except Exception as e:
        printError(str(e))
        printError(f"Could not read test case {testcase} and variable {testcase_variant}.")

    EVALUATIONDF = EVALUATIONDATA.copy()
    if not checksate:
        for norm in norms:
            EVALUATIONDF = EVALUATIONDF.drop([norm], axis=1)

    searchterm = testcase[2:]
    EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Test Case'] == searchterm].drop(['Test Case'], axis=1)
    EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Variable'] == testcase_variant].drop(['Variable'], axis=1)

    fig = px.line(resultDf, x="Time", y=resultDf.columns, template="simple_white", title=testcase_variant,
                  labels={"y": testcase_variant})
    fig.data[0].update(mode='markers')
    for figline in fig.data:
        figline.line.color = TOOLCOLORS[figline.name]

    namesDict = dict()
    for index, row in EVALUATIONDF.iterrows():
        namesDict[row['ToolID']] = f"{row['Tool Name']} ({row['Version']})"

    fig.update_layout(
        legend_title="Tools",
        yaxis_title=EVALUATIONDF["Unit"].iloc[0],
    )

    for figline in fig.data:
        if figline.name == "Reference":
            continue
        figline.name = namesDict[figline.name]



    def function(x):
        return '⭐⭐⭐' if x == 'Gold' else (
            '⭐⭐' if x == 'Silver' else (
                '⭐' if x == 'Bronze' else '-'
            ))

    EVALUATIONDF['SimQ-Rating'] = EVALUATIONDF['SimQ-Rating'].apply(function)

    return fig, EVALUATIONDF.drop(['index'], axis=1).to_dict('records'), ""

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
