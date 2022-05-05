# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Union, Any

import pandas
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

import sys

from plotly.graph_objs import Figure

sys.path.append('./scripts')

from ScoreCalculation import scoreCalculation

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.renderer = 'var renderer = new DashRenderer();'

PANDAS = dict()
PANDAS = scoreCalculation("./test_data", False)

app.layout = html.Div(style={"height": "100vh", 'display': 'flex', 'flex-direction': 'row'},
                      children=[

                          html.Div([
                              html.H1(
                                  children='SimQuality Test Cases',
                                  style={
                                      'textAlign': 'center',
                                  }
                              ),

                              html.Div([
                                  "Choose a test case",
                                  dcc.Dropdown(list(PANDAS.keys()), id="testcase-dropdown"),
                                  dcc.Dropdown(id="testcase-variant-dropdown")
                              ]),
                          ], style={'padding': 10, 'flex': "1 1 20%"}),

                          html.Div([
                              html.Div(children='Dash: A web application framework for your data.', style={
                                  'textAlign': 'center'
                              }),

                              dcc.Graph(
                                    id='testcase-graph',
                                    style={'height': 600},
                              )
                          ], style={'padding': 10, 'flex': "1 1 80%", "height": "100vh"}),

                      ])

@app.callback(
    Output('testcase-variant-dropdown', 'options'),
    Input('testcase-dropdown', 'value')
)
def update_var_dropdown(selected_testcase):
    test = list(PANDAS[selected_testcase].keys())
    return [{'label': i, 'value': i} for i in list(PANDAS[selected_testcase].keys())]


@app.callback(
    Output('testcase-graph', 'figure'),
    Input('testcase-dropdown', 'value'),
    Input('testcase-variant-dropdown', 'value')
)
def update_figure(selected_testcase, selected_variant):
    df = PANDAS[selected_testcase][selected_variant]
    fig = px.line(df, x="Date and Time", y=df.columns[1:], template="simple_white")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
