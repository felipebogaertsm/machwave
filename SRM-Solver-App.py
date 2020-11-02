import plotly.graph_objects as go
import numpy as np
import scipy.constants
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

web_res = 1000

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

material_list = [
    {'label': '6061-T6', 'value': '6061_t6'},
    {'label': '1045 steel', 'value': '1045_steel'},
    {'label': '304 stainless', 'value': '304_stainless'}
]

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
                            {'label': 'KNDX (Nakka)', 'value': 'kndx'},
                            {'label': 'KNER (Gudnason)', 'value': 'kner'},
                        ],
                        value='knsb-nakka'
                    )
                ]
            ),
            width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Grain segment count'),
                    dbc.Input(
                        placeholder='Set integer...',
                        id='N',
                        value='4',
                        type='number'
                    )
                ]
            ),
            width=6
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
                        placeholder='Insert grain diameter',
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

input_row_4 = html.Div([
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label('Segment configurations'),
                        dbc.Checklist(
                            options=[
                                {'label': 'Neutral burn profile', 'value': 'neutral_profile'},
                            ],
                            value=[False],
                            id='neutral_burn_profile',
                            switch=True,
                        ),
                        dbc.Checklist(
                            options=[
                                {'label': 'Single core diameter', 'value': True},
                            ],
                            value=[True],
                            id='single_core_diameter',
                            switch=True
                        )
                    ]
                ), width=12
            )
        ]
    )
])

input_row_5 = dbc.Row(
    [
        dbc.Col(
            id='core_diameter_inputs',
            children=[
                dbc.FormGroup(
                    children=[
                        dbc.Label('Segment length (mm)'),
                        dbc.Input(
                            placeholder='Insert segment length...',
                            id='D_core',
                            value='68',
                            type='number'
                        )
                    ]
                )
            ]
        ),
        dbc.Col(
            dbc.FormGroup(
                children=[
                    dbc.Label('Segment length (mm)'),
                    dbc.Input(
                        placeholder='Insert segment length...',
                        id='L_grain',
                        value='68',
                        type='number'
                    )
                ]
            )
        )
    ]
)

input_row_6 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Nozzle throat diameter (mm)'),
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
                    dbc.Label('Divergent angle (degrees)'),
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
                    dbc.Label('Convergent angle (degrees)'),
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

input_row_7 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Combustion chamber inside diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert inside diameter...',
                        id='D_in',
                        value='44.45',
                        type='number'
                    )
                ]
            ), width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Combustion chamber outside diameter (mm)'),
                    dbc.Input(
                        placeholder='Insert outside diameter...',
                        id='D_out',
                        value='50.8',
                        type='number'
                    )
                ]
            ), width=6
        )
    ]
)

input_row_8 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Structural safety factor'),
                    dbc.Input(
                        placeholder='Enter safety factor...',
                        id='sf',
                        type='number',
                        value='4'
                    )
                ]
            ), width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Nozzle material'),
                    dbc.Checklist(
                        options=[
                            {'label': 'Steel nozzle', 'value': 'steel_nozzle'}
                        ],
                        id='steel_nozzle',
                        switch=True,
                        value=True,
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
                    dbc.Label('Casing Material'),
                    dbc.Select(
                        options=material_list,
                        id='casing_material',
                        value=''
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
                    )
                ]
            )
        )
    ]
)

# _____________________________________________________________________________________________________________________
# GRAPHS

figure_grain_radial = go.Figure(
    data=go.Scatter(
        x=[0, 0],
        y=[0, 0]
    ),
    layout=go.Layout(
        title='Grain radial perspective',
        yaxis={'scaleanchor': 'x', 'scaleratio': 1}
    )
)

figure_grain_radial.add_shape(
    type='circle',
    xref='x', yref='y',
    fillcolor='#dac36d',
    x0=- 2, x1=2, y0=- 2, y1=2
)

figure_grain_radial.add_shape(
    type='circle',
    xref='x', yref='y',
    fillcolor='#e3e3e3',
    x0=- 1, x1=1, y0=- 1, y1=1
)

# _____________________________________________________________________________________________________________________
# INTERNAL BALLISTICS TAB

ib_row_1 = dbc.Row(
    [
        dbc.Col(
            html.Div(
                [
                    dbc.Label(
                        children=[
                            '.'
                        ]
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
                            input_row_5,
                            html.H2([dbc.Badge('Thrust chamber')]),
                            input_row_6,
                            input_row_7,
                            input_row_8,
                            input_row_9,
                        ]
                    )
                ),
                width=6
            ),
            dbc.Col(
                dbc.Card(
                    dcc.Graph(
                        id='grain_radial',
                        figure=figure_grain_radial
                    )
                ),
                width=6
            )
        ]
    )
])

ib_tab = dbc.Tab(
    label='Internal Ballistics',
    children=[
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H2([dbc.Badge('IB parameters')]),
                                html.H3([dbc.Badge('Burn Regression')]),
                                ib_row_1,
                            ]
                        )
                    ), width=6
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dcc.Graph(
                                    id='burn_regression_graph'
                                )
                            ]
                        )
                    ), width=6
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])

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


# _____________________________________________________________________________________________________________________
# CALLBACKS


@app.callback(
    [
        Output(component_id='burn_regression_graph', component_property='data')
    ],
    [
        Input(component_id='D_throat', component_property='value'),
        Input(component_id='grain_spacing', component_property='value'),
        Input(component_id='D_core', component_property='value'),
        Input(component_id='D_grain', component_property='value'),
        Input(component_id='N', component_property='value'),
        Input(component_id='L_grain', component_property='value'),
        Input(component_id='propellant_select', component_property='value'),
        Input(component_id='single_core_diameter', component_property='value')
    ]
)
def main_function(D_throat, grain_spacing, D_core, D_grain, N, L_grain, propellant, single_core_diameter):
    D_throat, grain_spacing, D_core, D_grain, N, L_grain = float(D_throat), float(grain_spacing), float(D_core), \
                                                           float(D_grain), int(N), float(L_grain)

    if single_core_diameter:
        D_core = np.ones(N) * D_core
        L_grain = np.ones(N) * L_grain

    # Pre-calculations and definitions:
    ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
    R_ch, R_ex = scipy.constants.R / M_ch, scipy.constants.R / M_ex
    T0 = ce * T0_ideal
    A_throat = getCircleArea(D_throat)
    L_cc = np.sum(L_grain) + (N - 1) * grain_spacing
    grain = BATES(web_res, N, D_grain, D_core, L_grain)
    # structure = MotorStructure(sf, m_motor, D_in, D_out, L_chamber, D_screw, D_clearance)

    # BATES grain calculation:
    w = grain.getWebArray()
    gAb = np.zeros((N, web_res))
    gVp = np.zeros((N, web_res))
    for j in range(N):
        for i in range(web_res):
            gAb[j, i] = grain.getBurnArea(w[j, i], j)
            gVp[j, i] = grain.getPropellantVolume(w[j, i], j)
    D_core_min_index = grain.getMinCoreDiameterIndex()
    for j in range(N):
        gAb[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gAb[j, :], left=0, right=0)
        gVp[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gVp[j, :], left=0, right=0)
    A_burn = gAb.sum(axis=0)
    V_prop = gVp.sum(axis=0)
    w = w[D_core_min_index, :]
    A_core = np.array([])
    for j in range(N):
        A_core = np.append(A_core, getCircleArea(D_core[j]))
    A_port = A_core[-1]
    initial_port_to_throat = A_port / A_throat
    burn_profile = burn_profile(A_burn)
    optimal_grain_length = grain.getOptimalSegmentLength()

    burn_regression_graph_data = [
        go.Scatter(
            x=w,
            y=A_burn
        )
    ]
    burn_regression_graph_dict = {
        'data': burn_regression_graph_data,
        'layout': go.Layout(title='Burn regression data')
    }

    return burn_regression_graph_dict


if __name__ == '__main__':
    app.run_server()
