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
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from ReadDashData import *

RESULTDIR = "dash_data"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets, title='SimQuality Dashboard')
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
info = readDashboardInformation()

try:
    TOOLCOLORS = readDict(os.path.join(RESULTDIR, "ToolColors.tsv"), False)
    TOOLCOLORS['Reference'] = "#000000"
except IOError as e:
    print(e)
    print(f"Could not read 'ToolColors.tsv' file.")
    exit(1)

app.layout = html.Div(
    style={'display': 'flex', 'flex-direction': 'row', 'box-sizing': 'border-box', 'height': '100vh'},
    children=[
        # left div
        html.Div([
            html.Img(src=app.get_asset_url('question-circle-solid.svg'),
                     id="open", className="info-icon"),

            html.Img(src=app.get_asset_url('SimQuality_Dashboard_Logo.png'),
                     style={'width': '400px'}),

            html.Div([
                dcc.Dropdown(
                    options=[{'label': str(i).replace("-", " "), 'value': i} for i in SUBDIRS],
                    id="testcase-dropdown",
                    value=SUBDIRS[0],
                ),
            ]),

            html.Div([
                html.Div([
                    html.Div([
                        html.Button('Download Aufgabenstellung inkl. Daten', id='btn-testcase-data', n_clicks=0),
                        dcc.Download(id="download-testcase-data")
                    ], style={'verticalAlign': 'middle', 'margin': '20px 0px'}),
                ]),
            ]),

            html.Div([
                html.Div(id='text-div', style={'margin': '10px 0px'}),
                html.Img(id="testcase-img", style={'margin': '20px auto'}),
            ]),

            dash_table.DataTable(
                id='weightfactor-table',
                editable=False,
                style_as_list_view=True,
                sort_action='native',
                css=[{"selector": ".show-hide", "rule": "display: none"}],
                hidden_columns=["index"],
                style_header_conditional=[
                            {
                                'if': {
                                    'column_id': 'statistical method'
                                },
                                'textAlign': 'left'
                            }
                ],
                style_data_conditional=[
                            {
                                'if': {
                                    'column_id': 'statistical method'
                                },
                                'textAlign': 'left'
                            }
                ]
            ),

            html.Div(id='error-div',
                     style={'margin': '10px 0px'}),


            html.Div(
                [
                    dbc.Modal(
                        [
                               dbc.ModalBody(
                                dcc.Markdown(id='dashboard-information', style={'margin': '10px 0px'}, children=info)
                            ),

                            html.Div([
                                dcc.Checklist(['Zeige Evaluierungsdaten'], [],
                                              id="statistical-checkstate", inline=True)
                            ]),

                            dbc.ModalFooter(
                                dbc.Button("Schließen", id="close", className="ml-auto")
                            ),
                        ],
                        id="modal",
                    ),
                ]
            ),
        ], style={'padding': 30, 'flex': "1 1 20%", 'background': '#9898982e',
                    'position': 'relative'}),

        # right dif div
        html.Div([

            dcc.Tabs(id="tabs-example-graph", value='overall-rating', children=[

                dcc.Tab(label='Gesamtbewertung', value='overall-rating', children=[

                    dash_table.DataTable(
                        id='rating-table',
                        editable=False,
                        style_as_list_view=True,
                        sort_action='native',
                        page_size=30,  # we have less data in this example, so setting to 20
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

                dcc.Tab(label='Erläuterung', value='comment', children=[

                    dcc.Markdown(id='comment-div', style={'margin': '10px 0px'})

                ]),

                dcc.Tab(label='Variablenanalyse', value='variable-analysis', children=[

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

            ]),


        ], style={'padding': 30, 'flex': "1 1 80%"}),

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
    Output('text-div', 'children'),
    Output('comment-div', 'children'),
    Output('testcase-img', 'src'),
    Output('rating-table', 'data'),
    Output('weightfactor-table', 'data'),
    Input('testcase-dropdown', 'value'),
    Input('statistical-checkstate', 'value')
)
def clean_data(selected_testcase, checkstate):
    # some expensive data processing step
    try:
        testCaseDescription = readTestCaseDescriptionFile(RESULTDIR, selected_testcase)
        testCaseComment = readCommentFile(RESULTDIR, selected_testcase)
        image = f"{selected_testcase[0:4]}.png"
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

    weightFactorDf = pd.DataFrame()

    if checkstate:
        weightFactorDf = pd.read_csv(os.path.join(RESULTDIR, selected_testcase, "WeightFactors.tsv"), encoding='utf-8', sep="\t",
                                     engine="pyarrow").reset_index()

        weightFactorDf = weightFactorDf.drop(weightFactorDf[weightFactorDf['weight factor [-]'] == 0].index)

    return [{'label': i, 'value': i} for i in variables], \
           variables[0], testCaseDescription, testCaseComment, \
           app.get_asset_url(image), ratingDf.to_dict('records'), \
           weightFactorDf.to_dict('records')


# Figure is updated
@app.callback(
    [Output('testcase-graph', 'figure'),
    Output('evaluation-table', 'data'),
    Output('loading-data', 'children')],
    Input('testcase-variant-dropdown', 'value'),
    State('testcase-dropdown', 'value'),
    Input('statistical-checkstate', 'value')
)
def update_testcase_variant_data(testcase_variant, testcase, checksate):
    norms = ['CVRMSE [%]','Daily Amplitude CVRMSE [%]','MBE','RMSEIQR [%]','MSE [%]','NMBE [%]','Average [-]',
             'NRMSE [%]','RMSE [%]','RMSLE [%]','R squared [-]','std dev [-]','Maximum [-]','Minimum [-]','Fehlercode',
             'Max Difference [-]']

    #### READING ALL EVALUATION DATA ####
    try:
        print(f"\n##################################################\n")
        print(f"Reading test case '{testcase}' and variable '{testcase_variant}'.")

        resultDf = readDashData(RESULTDIR, testcase, testcase_variant)

        print(f"Converting 'result.tsv' with evaluation results.")
        EVALUATIONDF = EVALUATIONDATA.copy()
        print(EVALUATIONDF)
        if not checksate:
            for norm in norms:
                if norm in EVALUATIONDF.columns:
                    EVALUATIONDF = EVALUATIONDF.drop([norm], axis=1)

        searchterm = testcase[2:]
        print(f"Reading data for search term '{searchterm}'.")
        print(EVALUATIONDF)

        EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Test Case'] == searchterm].drop(['Test Case'], axis=1)
        EVALUATIONDF = EVALUATIONDF.loc[EVALUATIONDF['Variable'] == testcase_variant].drop(['Variable'], axis=1)

        namesDict = dict()
        for index, row in EVALUATIONDF.iterrows():
            namesDict[row['ToolID']] = f"{row['Tool Name']} ({row['Version']})"


    except Exception as e:
        print(str(e))
        print(f"Could not read evaluation data of test case '{testcase}' and variant '{testcase_variant}'")
        raise PreventUpdate

    #### UPDATING RESULT DIAGRAM ####
    try:
        print(f"Updating figure with all needed data.")
        fig = px.line(resultDf, x="Time", y=resultDf.columns, template="simple_white", title=testcase_variant,
                      labels={"y": testcase_variant})
        fig.data[0].update(mode='markers')
        for figline in fig.data:
            figline.line.color = TOOLCOLORS[figline.name]

        fig.update_layout(
            legend_title="Tools",
            yaxis_title=EVALUATIONDF["Unit"].iloc[0],
        )

        for figline in fig.data:
            if figline.name == "Reference":
                continue
            if figline.name not in namesDict.keys():
                continue
            figline.name = namesDict[figline.name]
    except Exception as e:
        print(str(e))
        print(f"Could not update figure of test case '{testcase}' and variant '{testcase_variant}'")
        raise PreventUpdate

    print(f"Converting rating to coloring.")

    def function(x):
        return '🟩' if x == 'Gold' else (
            '🟨' if x == 'Silver' else (
                '🟨' if x == 'Bronze' else '🟥'
            ))

    EVALUATIONDF['SimQ-Rating'] = EVALUATIONDF['SimQ-Rating'].apply(function)

    def functionReference(x):
        return '✔️' if x == True else ''

    EVALUATIONDF['Reference'] = EVALUATIONDF['Reference'].apply(functionReference)
    EVALUATIONDF = EVALUATIONDF.drop(['index'], axis=1).to_dict('records')

    return fig, EVALUATIONDF, ""

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
        zipTestCaseData(f"./dash_data/{value}/download_data", f"{value}-data")
    )

@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.title = "SimQuality Dashboard"
    app.run_server(debug=True)
