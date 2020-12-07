import plotly.graph_objects as go
import numpy as np
import scipy.constants
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from functions.InternalBallistics import *
from functions.Propellant import *
from functions.MotorStructure import *
from functions.functions import *

# _____________________________________________________________________________________________________________________
# INITIAL DEFINITIONS

web_res = 1000
dt = 0.01
ddt = 10

# Input label column width:
label_col_width = 1
# Input object column width:
input_col_width = 2

# Number of input boxes of grain cores:
number_grain_core_inputs = 8

prop_dict = {
    'KNSB (Nakka)': 'knsb-nakka',
    'KNSB (Gudnason)': 'knsb',
    'KNER (Gudnason)': 'kner',
    'KNDX (Nakka)': 'kndx'
}

material_list = [
    {'label': '6061-T6', 'value': '6061_t6'},
    {'label': '1045 steel', 'value': '1045_steel'},
    {'label': '304 stainless', 'value': '304_stainless'}
]

# Dash core diameter callback input:
core_input = [Input(component_id=f'D_core_{i + 1}', component_property='value')
              for i in range(number_grain_core_inputs)]

# _____________________________________________________________________________________________________________________
# INPUT TAB

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
            width=6
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
            width=6
        )
    ]
)

input_row_2 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Propellant composition'),
                    dbc.Select(
                        id='propellant_select',
                        options=[
                            {'label': 'KNSB (Nakka)', 'value': 'knsb-nakka'},
                            {'label': 'KNSB (Gudnason)', 'value': 'knsb'},
                            {'label': 'KNER (Gudnason)', 'value': 'kner'},
                            {'label': 'KNDX (Nakka)', 'value': 'kndx'},
                        ],
                        value='knsb-nakka'
                    )
                ]
            ),
            width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain segment count'),
                    daq.NumericInput(
                        id='N',
                        value=4,
                        min=1,
                        max=8
                    )
                ]
            ),
            width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    daq.BooleanSwitch(
                        id='neutral_burn_profile',
                        label='Neutral burn profile',
                        on=True
                    )
                ]
            ), width=4
        )
    ]
)

input_row_3 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert grain diameter...',
                        id='D_grain',
                        value='41',
                        type='number'
                    )
                ]
            ),
            width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain spacing (mm)'),
                    dbc.Input(
                        placeholder='Insert grain spacing...',
                        id='grain_spacing',
                        value='2',
                        type='number'
                    )
                ]
            )
        )
    ]
)

input_row_4 = dbc.Row(
    [
        dbc.Col(
            id='core_diameter_inputs',
            children=[dbc.FormGroup(
                children=[
                    dbc.Label(f'Core #{i + 1} diameter (mm)'),
                    dbc.Input(
                        placeholder=f'Insert #{i + 1} core diameter...',
                        id=f'D_core_{i + 1}',
                        value='15',
                        type='number'
                    )
                ]
            ) for i in range(number_grain_core_inputs)]
        ),
        dbc.Col(
            id='segment_length_inputs',
            children=[dbc.FormGroup(
                children=[
                    dbc.Label(f'Length of segment #{i + 1} (mm)'),
                    dbc.Input(
                        placeholder=f'Insert #{i + 1} length segment...',
                        id=f'L_grain_{i + 1}',
                        value='68',
                        type='number'
                    )
                ]
            ) for i in range(number_grain_core_inputs)]
        )
    ]
)

input_row_5 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Throat diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert throat diameter...',
                        id='D_throat',
                        value='9.5',
                        type='number'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Divergent angle (°)'),
                    dbc.Input(
                        placeholder='Enter divergent angle...',
                        id='Div_angle',
                        value='12',
                        type='number'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Convergent angle (°)'),
                    dbc.Input(
                        placeholder='Enter convergent angle...',
                        id='Conv_angle',
                        value='30',
                        type='number'
                    )
                ]
            ), width=4
        )
    ]
)

input_row_6 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Inside diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert inside diameter...',
                        id='D_in',
                        value='44.45',
                        type='number'
                    ),
                    dbc.FormText('Including the thermal liner!'),
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Outside diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert outside diameter...',
                        id='D_out',
                        value='50.8',
                        type='number'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Liner thickness (mm)'),
                    dbc.Input(
                        placeholder='Insert liner thickness...',
                        id='liner_thickness',
                        value='1',
                        type='number'
                    )
                ]
            ), width=4
        )
    ]
)

input_row_7 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Safety factor'),
                    dbc.Input(
                        placeholder='Enter safety factor...',
                        id='sf',
                        type='number',
                        value='4'
                    )
                ]
            ), width=3
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Screw diam. (mm)'),
                    dbc.Input(
                        placeholder='Enter screw diameter...',
                        id='D_screw',
                        type='number',
                        value='4.2'
                    ),
                    dbc.FormText('Excluding threads!')
                ]
            ), width=3
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Screw clearance (mm)'),
                    dbc.Input(
                        placeholder='Enter screw clearance diameter...',
                        id='D_clearance',
                        type='number',
                        value='5.0'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    daq.BooleanSwitch(
                        id='steel_nozzle',
                        label='Steel nozzle',
                        on=True
                    )
                ]
            ), width=2
        )
    ]
)

input_row_8 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Casing Material'),
                    dbc.Select(
                        options=material_list,
                        id='casing_material',
                        value='6061_t6',
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Nozzle material'),
                    dbc.Select(
                        options=material_list,
                        id='nozzle_material',
                        value='304_stainless',
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Bulkhead material'),
                    dbc.Select(
                        options=material_list,
                        id='bulkhead_material',
                        value='6061_t6',
                    )
                ]
            )
        )
    ]
)

input_row_9 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Rocket mass w/o the motor (kg)'),
                    dbc.Input(
                        placeholder='Enter the rocket mass without the motor...',
                        id='mass_wo_motor',
                        type='number',
                        value='2.8'
                    )
                ]
            ), width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Motor structural mass (kg)'),
                    dbc.Input(
                        placeholder='Enter the motor structural mass...',
                        id='m_motor',
                        type='number',
                        value='0.85'
                    )
                ]
            ), width=6
        )
    ]
)

input_row_10 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Rocket drag coefficient'),
                    dbc.Input(
                        placeholder='Enter the drag coefficient of the rocket...',
                        id='Cd',
                        type='number',
                        value='0.4'
                    )
                ]
            ), width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Frontal diameter (mm)'),
                    dbc.Input(
                        placeholder='Enter the rocket frontal diameter...',
                        id='D_rocket',
                        type='number',
                        value='67.5'
                    )
                ]
            ), width=6
        )
    ]
)

# _____________________________________________________________________________________________________________________
# GRAPHS

# _____________________________________________________________________________________________________________________
# INTERNAL BALLISTICS TAB

ib_rows = dbc.Row(
    [
        dbc.Col(
            html.Div(
                [
                    dbc.Label(
                        children=[],
                        id='max_P0'
                    )
                ]
            )
        )
    ]
)

# _____________________________________________________________________________________________________________________
# TABS

input_tab = dbc.Tab(label='Inputs', children=[
    dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H2([dbc.Badge('Motor data')]),
                            input_row_1,
                            html.H2([dbc.Badge('Propellant grain')]),
                            input_row_2,
                            input_row_3,
                            html.H3([dbc.Badge('Grain segments')]),
                            input_row_4,
                            html.H2([dbc.Badge('Thrust chamber')]),
                            input_row_5,
                            html.H3([dbc.Badge('Combustion chamber')]),
                            input_row_6,
                            input_row_7,
                            input_row_8,
                            html.H2([dbc.Badge('Vehicle data')]),
                            input_row_9,
                            input_row_10,
                            dbc.Button('Run Simulation', color='primary', id='run_ballistics')
                        ]
                    )
                ),
                width=6
            ),
            dbc.Col(
                dbc.Card(
                    dcc.Graph(
                        id='grain_radial',
                        figure={}
                    )
                ),
                width=6
            )
        ]
    )
])

ib_tab = dbc.Tab(
    label='Internal Ballistics',
    id='ib_tab',
    disabled=False,
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id='burn_regression_graph',
                                    figure={}
                                )
                            ]
                        )
                    ), width=8
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2([dbc.Badge('IB parameters')]),
                                html.H3([dbc.Badge('Burn Regression')]),
                                ib_rows,
                            ]
                        )
                    ), width=4
                )
            ]
        )
    ]
)

nozzle_tab = dbc.Tab(
    label='Nozzle Design',
    children=[
        html.P('.')
    ]
)

structure_tab = dbc.Tab(
    label='Structure',
    children=[
        html.P('.')
    ]
)

ta_tab = dbc.Tab(
    label='Thermal Analysis',
    children=[
        html.P('.')
    ]
)

ballistic_tab = dbc.Tab(
    label='Rocket Trajectory',
    children=[
        html.P('.')
    ]
)

# _____________________________________________________________________________________________________________________
# DASH APP EXECUTION

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("SRM Solver", style={'textAlign': 'center'}),
            html.H5('Build a BATES grain Solid Rocket Motor inside your own browser', style={'textAlign': 'center'}),
        ],
            width={'size': 12}
        )
    ],
    ),
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


# _____________________________________________________________________________________________________________________
# CALLBACKS


@app.callback(
    Output(component_id='grain_radial', component_property='figure'),
    [
        Input(component_id='D_grain', component_property='value'),
        Input(component_id='D_core_1', component_property='value')
    ]
)
def update_grain_radial_graph(D_grain, D_core):
    D_grain = float(D_grain)
    D_core = float(D_core)
    R_grain = D_grain / 2
    R_core = D_core / 2
    x = np.linspace(0.5 * - 1 * D_grain, 0.5 * D_grain)
    figure_grain_radial = go.Figure(
        data=go.Scatter(
            x=[0, R_grain],
            y=[R_core, 0]
        ),
        layout=go.Layout(
            title='Grain radial perspective',
            yaxis={'scaleanchor': 'x', 'scaleratio': 1},
        )
    )
    figure_grain_radial.add_shape(
        type='circle',
        xref='x', yref='y',
        fillcolor='#dac36d',
        x0=- R_grain, x1=R_grain, y0=- R_grain, y1=R_grain
    )
    figure_grain_radial.add_shape(
        type='circle',
        xref='x', yref='y',
        fillcolor='#e3e3e3',
        x0=- R_core, x1=R_core, y0=- R_core, y1=R_core
    )
    return figure_grain_radial


# # Update the length input boxes:
# @app.callback(
#     Output(component_id='segment_length_inputs', component_property='children'),
#     [
#         Input(component_id='neutral_burn_profile', component_property='on'),
#         Input(component_id='N', component_property='value'),
#         Input(component_id='D_grain', component_property='value'),
#         Input(component_id='D_core_1', component_property='value'),
#         Input(component_id='D_core_2', component_property='value'),
#         Input(component_id='D_core_3', component_property='value'),
#         Input(component_id='D_core_4', component_property='value'),
#         Input(component_id='D_core_5', component_property='value'),
#         Input(component_id='D_core_6', component_property='value'),
#         Input(component_id='D_core_7', component_property='value'),
#         Input(component_id='D_core_8', component_property='value')
#     ]
# )
# def update_length_input_box(
#         neutral_burn_profile, N, D_grain, D_core_1, D_core_2, D_core_3, D_core_4, D_core_5, D_core_6, D_core_7, D_core_8
# ):
#     D_core = np.array([float(D_core_1), float(D_core_2), float(D_core_3), float(D_core_4), float(D_core_5),
#                        float(D_core_6), float(D_core_7), float(D_core_8)])
#     D_grain = float(D_grain)
#     N = int(N)
#     if neutral_burn_profile:
#         length_col = [dbc.FormGroup(
#             children=[
#                 dbc.Label('Segment length (mm)'),
#                 dbc.Input(
#                     placeholder='Insert segment length...',
#                     id='L_grain',
#                     value=f'{0.5 * (3 * D_grain + D_core[i])}',
#                     type='number',
#                     disabled=True
#                 )
#             ]
#         ) for i in range(number_grain_core_inputs)]
#     else:
#         length_col = [dbc.FormGroup(
#             children=[
#                 dbc.Label(f'Segment #{i + 1} length (mm)'),
#                 dbc.Input(
#                     placeholder=f'Insert #{i + 1} segment length...',
#                     id=f'L_grain_{i + 1}',
#                     value='',
#                     type='number',
#                     disabled=False
#                 )
#             ]
#         ) for i in range(number_grain_core_inputs)]
#     return length_col


# @app.callback(
#     State(component_id='run_ballistics', component_property='n_clicks'),
#     [
#         Output(component_id='burn_regression_graph', component_property='figure'),
#         Output(component_id='max_P0', component_property='children')
#     ],
#     [
#         Input(component_id='N', component_property='value'),
#         Input(component_id='D_grain', component_property='value'),
#         Input(component_id='D_core_1', component_property='value'),
#         Input(component_id='D_core_2', component_property='value'),
#         Input(component_id='D_core_3', component_property='value'),
#         Input(component_id='D_core_4', component_property='value'),
#         Input(component_id='D_core_5', component_property='value'),
#         Input(component_id='D_core_6', component_property='value'),
#         Input(component_id='D_core_7', component_property='value'),
#         Input(component_id='D_core_8', component_property='value'),
#         Input(component_id='L_grain_1', component_property='value'),
#         Input(component_id='L_grain_2', component_property='value'),
#         Input(component_id='L_grain_3', component_property='value'),
#         Input(component_id='L_grain_4', component_property='value'),
#         Input(component_id='L_grain_5', component_property='value'),
#         Input(component_id='L_grain_6', component_property='value'),
#         Input(component_id='L_grain_7', component_property='value'),
#         Input(component_id='L_grain_8', component_property='value'),
#         Input(component_id='sf', component_property='value'),
#         Input(component_id='m_motor', component_property='value'),
#         Input(component_id='mass_wo_motor', component_property='value'),
#         Input(component_id='D_in', component_property='value'),
#         Input(component_id='D_out', component_property='value'),
#         Input(component_id='liner_thickness', component_property='value'),
#         Input(component_id='grain_spacing', component_property='value'),
#         Input(component_id='D_screw', component_property='value')
#     ]
# )
# def burn_regression():
#     pass


if __name__ == '__main__':
    app.run_server()
