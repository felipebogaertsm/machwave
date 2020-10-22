import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output
from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
from functions.functions import *

app = dash.Dash()

app.layout = html.Div([

    html.Div([
        html.P(html.Label('SRM Solver'))
    ]), 

    html.Div([
        html.P(html.Label('Propellant')),
        dcc.Dropdown(options=[{'label': 'KNSB (Nakka)', 'value': 'knsb-nakka'},
                              {'label': 'KNSB (Gudnason)', 'value': 'knsb'},
                              {'label': 'KNDX (Nakka)', 'value': 'kndx'},
                              {'label': 'KNER (Gudnason)', 'value': 'kner'},
                              {'label': 'KNSU (Nakka)', 'value': 'knsu'}
                              ],
                     value='kner')
    ]),

    html.Div([
        html.P(html.Label('Grain count')),
        dcc.Slider(min=1, max=10, step=1, value=4, marks={i: i for i in range(1, 10)})
    ]),

    html.Div([
        dcc.Input(id='motor_name', value='', type='text'),
        html.Div(id='my-div')
    ])

])


@app.callback(Output(component_id='my-div', component_property='children'),
              [Input(component_id='my-id', component_property='value')])
def update_output_div(input_value):
    return "You entered: {}".format(input_value)


if __name__ == '__main__':
    app.run_server()
