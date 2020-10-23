import plotly.graph_objects as go
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
from functions.functions import *

# _____________________________________________________________________________________________________________________
# INITIAL DEFINITIONS

# Input label column width:
label_col_width = 1
# Input object column width:
input_col_width = 2

# _____________________________________________________________________________________________________________________
# DASH COMPONENTS

title_row = dbc.Row([
    dbc.Col(html.H1("SRM Solver"),
            width={'size': 6, 'offset': 0},
            )
])

input_row_1 = dbc.Row([
    dbc.Col(
        html.Label('Motor Name: '),
        width=label_col_width
    ),
    dbc.Col(
        html.Div([
            dbc.Input(
                placeholder='Insert text...', id='motor_name', value='', type='text'
            )
        ]),
        width=input_col_width
    ),
    dbc.Col(
        html.Label('Manufacturer: '),
        width=label_col_width
    ),
    dbc.Col(
        html.Div([
            dbc.Input(
                placeholder='Insert text...', id='motor_manuf', value='', type='text'
            )
        ]),
        width=input_col_width
    )
])

input_row_2 = dbc.Row([
    dbc.Col(
        html.Label('Propellant: '),
        width=1
    ),
    dbc.Col(
        dcc.Dropdown(
            options=[
                {'label': 'KNSB (Nakka)', 'value': 'knsb-nakka'},
                {'label': 'KNSB (Gudnason)', 'value': 'knsb'},
                {'label': 'KNDX (Nakka)', 'value': 'kndx'},
                {'label': 'KNER (Gudnason)', 'value': 'kner'},
                {'label': 'KNSU (Nakka)', 'value': 'knsu'}
            ],
            placeholder='Select propellant...'
        ),
        width=2
    ),
    dbc.Col(
        html.Label(['Grain Count: ', dbc.Input(placeholder='Set integer...', id='N', value='4', type='number')]),
        width={'size': 3, 'offset': 1}
    )
], no_gutters=False)

input_row_3 = dbc.Row([
    dbc.Col(
        html.Label(['Grain Diameter: ',
                    dbc.Input(placeholder='Insert value...', id='D_grain', value='', type='text')
                    ]),
        width=3
    )
])

input_row_4 = dbc.Row([
    dbc.Col(
        dcc.Dropdown(
            id='grain_dropdown',
            searchable=False,
            clearable=False,
            placeholder='Select a grain...'
        ),
        width=6
    )
])

input_row_5 = dbc.Row([
    dbc.Col(
        html.Label(['Grain core diameter: ',
                    dbc.Input(placeholder='Insert value...', id='D_core', value='', type='number')
                    ]),
        width=3
    )

])

# _____________________________________________________________________________________________________________________
# DASH APP EXECUTION

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

app.layout = html.Div([

    title_row,

    dcc.Tabs([
        dcc.Tab(label='Inputs', children=[
            dbc.Card(
                dbc.CardBody([
                    html.P(''),
                    html.H2('Motor Data'),
                    input_row_1,
                    html.P(''),
                    html.H2('Propellant Data'),
                    input_row_2,
                    input_row_3,
                    html.P(''),
                    html.H3('Grain segments'),
                    input_row_4
                ]))
        ]),
        dcc.Tab(label='Internal Ballistics', children=[
            html.P('.')
        ]),
        dcc.Tab(label='Structure', children=[
            html.P('.')
        ]),
        dcc.Tab(label='Thermal Analysis', children=[
            html.P('.')
        ]),
        dcc.Tab(label='Ballistic', children=[
            html.P('.')
        ])
    ])

])


@app.callback(Output(component_id='grain_dropdown', component_property='options'),
              [Input(component_id='N', component_property='value')])
def update_grain_count(input_value):
    options = [
        {'label': f'Grain #{n + 1}'} for n in range(int(float(input_value)))
    ]
    return options


if __name__ == '__main__':
    app.run_server()
