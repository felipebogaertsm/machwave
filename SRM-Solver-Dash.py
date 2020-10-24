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

prop_dict = {
    'KNSB (Nakka)': 'knsb-nakka',
    'KNSB (Gudnason)': 'knsb',
    'KNER (Gudnason)': 'kner',
    'KNDX (Nakka)': 'kndx'
}

# _____________________________________________________________________________________________________________________
# INPUT COMPONENTS

input_row_1 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Name'),
                    dbc.Input(
                        type='text',
                        id='motor_name',
                        placeholder='Enter motor name...'
                    )
                ]
            ),
            width=3
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Manufacturer'),
                    dbc.Input(
                        type='text',
                        id='motor_manufacturer',
                        placeholder='Enter motor manufacturer...'
                    )
                ]
            ),
            width=3
        )
    ]
)

input_row_2 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Propellant'),
                    dbc.Select(
                        id='propellant_select',
                        options=[
                            {'label': 'KNSB (Nakka)', 'value': 'knsb-nakka'},
                            {'label': 'KNSB (Gudnason)', 'value': 'knsb'},
                            {'label': 'KNDX', 'value': 'kndx'},
                            {'label': 'KNER', 'value': 'kner'},
                        ],
                    )
                ]
            ),
            width=3
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain count'),
                    dbc.Input(
                        placeholder='Set integer...',
                        id='N',
                        value='4',
                        type='number'
                    )
                ]
            ),
            width=3
        )
    ]
)

input_row_3 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain diameter'),
                    dbc.Input(
                        placeholder='Insert grain diameter',
                        id='D_grain',
                        value='',
                        type='number'
                    )
                ]
            ),
            width=3
        ),
        dbc.Col(
            dbc.Checklist(
                options=[
                    {'label': 'Neutral burn profile', 'value': True},
                ],
                value=[],
                id='neutral_burn_profile',
                switch=True,
            ),
            width=3
        )
    ]
)

input_row_4 = dbc.Row([
    dbc.Col(
        html.Label(['Grain core diameter: ',
                    dbc.Input(placeholder='Insert value...', id='D_core', value='', type='number')
                    ]),
        width=3
    )

])

# _____________________________________________________________________________________________________________________
# TABS

input_tab = dbc.Tab(label='Inputs', children=[
    dbc.Card(
        dbc.CardBody([
            html.H2([dbc.Badge('Motor Data')]),
            input_row_1,
            html.H2([dbc.Badge('Propellant')]),
            input_row_2,
            input_row_3,
            html.H3([dbc.Badge('Grain segments')]),
            input_row_4
        ])
    )
])

ib_tab = dbc.Tab(label='Internal Ballistics', children=[
    html.P('.')
])

structure_tab = dbc.Tab(label='Structure', children=[
    html.P('.')
])

ta_tab = dbc.Tab(label='Thermal Analysis', children=[
    html.P('.')
])

ballistic_tab = dbc.Tab(label='Ballistic', children=[
    html.P('.')
])

# _____________________________________________________________________________________________________________________
# DASH APP EXECUTION

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

app.layout = html.Div([

    dbc.Row([
        dbc.Col([
            html.H1("SRM Solver", style={'textAlign': 'center'}),
            html.H5('Build a BATES grain Solid Rocket Motor inside your own browser', style={'textAlign': 'center'})
        ],
            width={'size': 12}
        )
    ]),

    dbc.Tabs([
        input_tab,
        ib_tab,
        structure_tab,
        ta_tab,
        ballistic_tab
    ]),

    html.Div([
        dcc.Markdown('Written by Felipe Bogaerts de Mattos, October 2020.', style={'textAlign': 'right'})
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
