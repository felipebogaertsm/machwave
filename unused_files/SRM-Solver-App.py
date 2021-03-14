import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output, State

from functions.Ballistics import *
from functions.InternalBallistics import *
from functions.MotorStructure import *
from functions.Simulation import *
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
                        value='4',
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
            ), width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Expansion ratio'),
                    dbc.Input(
                        placeholder='Insert the expansion ratio...',
                        id='Exp_ratio',
                        value='9',
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

input_row_7 = dbc.Row(
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

input_row_8 = dbc.Row(
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

input_row_9 = dbc.Row(
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

input_row_10 = dbc.Row(
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

input_row_11 = dbc.Row(
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

input_row_12 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Drogue activation time [s]'),
                    dbc.Input(
                        placeholder='Enter value...',
                        id='drogue_time',
                        type='number',
                        value='1'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Drogue drag coefficient'),
                    dbc.Input(
                        id='Cd_drogue',
                        type='number',
                        value='1.75'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Drogue diameter [m]'),
                    dbc.Input(
                        id='D_drogue',
                        value='1.25'
                    )
                ]
            ), width=4
        )
    ]
)

input_row_13 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Main drag coefficient'),
                    dbc.Input(
                        id='Cd_main',
                        type='number',
                        value='2',
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Main diameter [m]'),
                    dbc.Input(
                        id='D_main',
                        type='number',
                        value='2.66',
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Main activation height [m]'),
                    dbc.Input(
                        id='main_chute_activation_height',
                        value='500',
                        type='number'
                    )
                ]
            ), width=4
        )
    ]
)

input_row_14 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Time step (s)'),
                    dbc.Input(
                        placeholder='Enter the time step...',
                        id='dt',
                        type='number',
                        value='0.01'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Time step multiplier'),
                    dbc.Input(
                        placeholder='Enter value...',
                        id='ddt',
                        type='number',
                        value='10'
                    )
                ]
            ), width=4
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('.eng resolution'),
                    dbc.Input(
                        placeholder='Enter value...',
                        id='eng_res',
                        type='number',
                        value='25'
                    )
                ]
            )
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
                            html.H3('Motor data'),
                            input_row_1,
                            html.Br(),
                            html.H3('Propellant grain'),
                            input_row_2,
                            input_row_3,
                            html.Br(),
                            html.H3('Grain segments'),
                            input_row_4,
                            html.Br(),
                            html.H3('Thrust chamber'),
                            input_row_5,
                            input_row_6,
                            html.Br(),
                            html.H3('Combustion chamber'),
                            input_row_7,
                            input_row_8,
                            input_row_9,
                            html.Br(),
                            html.H3('Vehicle data'),
                            input_row_10,
                            input_row_11,
                            html.Br(),
                            html.H3('Recovery data'),
                            input_row_12,
                            input_row_13,
                            html.H3('Simulation settings'),
                            input_row_14,
                            html.Hr(),
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
                                html.H3('IB parameters'),
                                html.H3('Burn Regression'),
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

theme = {
    'dark': False,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E'
}

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("SRM Solver", style={'textAlign': 'center'}),
            html.H5('Build a BATES grain Solid Rocket Motor inside your own browser', style={'textAlign': 'center'}),
        ],
            width={'size': 12}
        ),
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
            title='Grain #1 radial perspective',
            yaxis={'scaleanchor': 'x', 'scaleratio': 1},
            plot_bgcolor='rgba(0,0,0,0)'
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


@app.callback(
    [
        Output(component_id='burn_regression_graph', component_property='figure'),
        Output(component_id='max_P0', component_property='children')
    ],
    [
        Input(component_id='N', component_property='value'),
        Input(component_id='D_grain', component_property='value'),
        Input(component_id='D_core_1', component_property='value'),
        Input(component_id='D_core_2', component_property='value'),
        Input(component_id='D_core_3', component_property='value'),
        Input(component_id='D_core_4', component_property='value'),
        Input(component_id='D_core_5', component_property='value'),
        Input(component_id='D_core_6', component_property='value'),
        Input(component_id='D_core_7', component_property='value'),
        Input(component_id='D_core_8', component_property='value'),
        Input(component_id='L_grain_1', component_property='value'),
        Input(component_id='L_grain_2', component_property='value'),
        Input(component_id='L_grain_3', component_property='value'),
        Input(component_id='L_grain_4', component_property='value'),
        Input(component_id='L_grain_5', component_property='value'),
        Input(component_id='L_grain_6', component_property='value'),
        Input(component_id='L_grain_7', component_property='value'),
        Input(component_id='L_grain_8', component_property='value'),
        Input(component_id='propellant_select', component_property='value'),
        Input(component_id='sf', component_property='value'),
        Input(component_id='m_motor', component_property='value'),
        Input(component_id='mass_wo_motor', component_property='value'),
        Input(component_id='Cd', component_property='value'),
        Input(component_id='D_rocket', component_property='value'),
        Input(component_id='D_in', component_property='value'),
        Input(component_id='D_out', component_property='value'),
        Input(component_id='liner_thickness', component_property='value'),
        Input(component_id='grain_spacing', component_property='value'),
        Input(component_id='D_throat', component_property='value'),
        Input(component_id='Exp_ratio', component_property='value'),
        Input(component_id='D_screw', component_property='value'),
        Input(component_id='D_clearance', component_property='value'),
        Input(component_id='Div_angle', component_property='value'),
        Input(component_id='Conv_angle', component_property='value'),
        Input(component_id='casing_material', component_property='value'),
        Input(component_id='nozzle_material', component_property='value'),
        Input(component_id='bulkhead_material', component_property='value'),
        Input(component_id='D_drogue', component_property='value'),
        Input(component_id='Cd_drogue', component_property='value'),
        Input(component_id='drogue_time', component_property='value'),
        Input(component_id='D_main', component_property='value'),
        Input(component_id='Cd_main', component_property='value'),
        Input(component_id='main_chute_activation_height', component_property='value')
    ],
    State(component_id='run_ballistics', component_property='n_clicks'),
)
def burn_regression(
        N, D_grain,
        D_core_1, D_core_2, D_core_3, D_core_4, D_core_5, D_core_6, D_core_7, D_core_8,
        L_grain_1, L_grain_2, L_grain_3, L_grain_4, L_grain_5, L_grain_6, L_grain_7, L_grain_8,
        propellant, sf, m_motor, mass_wo_motor, Cd, D_rocket, D_in, D_out, liner_thickness, grain_spacing, D_throat,
        Exp_ratio, D_screw, D_clearance, Div_angle, Conv_angle, casing_material, nozzle_material, bulkhead_material,
        D_drogue, Cd_drogue, drogue_time, D_main, Cd_main, main_chute_activation_height
):
    N, D_grain = float(N), float(D_grain)

    Y_chamber = 255e6
    Y_nozzle = 205e6
    Y_bulkhead = 255e6
    U_screw = 500e6
    max_number_of_screws = 30
    C1 = 0.00506
    C2 = 0.00000
    h0 = 645
    P_igniter = 1e6
    rail_length = 5

    D_core = np.array([float(D_core_1), float(D_core_2), float(D_core_3), float(D_core_4), float(D_core_5),
                       float(D_core_6), float(D_core_7), float(D_core_8)])
    L_grain = np.array([float(L_grain_1), float(L_grain_2), float(L_grain_3), float(L_grain_4), float(L_grain_5),
                        float(L_grain_6), float(L_grain_7), float(L_grain_8)])

    # Converting variables to float and SI units:
    D_core, L_grain = D_core[: N - 1] * 1e-3, L_grain[: N - 1] * 1e-3
    D_grain = float(D_grain) * 1e-3
    D_rocket = float(D_rocket) * 1e-3
    D_in, D_out = float(D_in) * 1e-3, float(D_out) * 1e-3
    liner_thickness = float(liner_thickness) * 1e-3
    sf = float(sf)
    grain_spacing = float(grain_spacing) * 1e-3
    D_throat = float(D_throat) * 1e-3
    Exp_ratio = float(Exp_ratio)
    D_screw = float(D_screw) * 1e-3
    D_clearance = float(D_clearance) * 1e-3
    D_drogue = float(D_drogue)
    D_main = float(D_main)
    m_motor = float(m_motor)
    mass_wo_motor = float(mass_wo_motor)

    # The propellant name input above triggers the function inside 'Propellant.py' to return the required data.
    n_ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
    # Getting PropellantSelected class based on previous input:
    propellant_data = PropellantSelected(
        n_ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex
    )
    # Combustion chamber length [m]:
    L_chamber = np.sum(L_grain) + (N - 1) * grain_spacing
    # Combustion chamber inner diameter (casing inner diameter minus liner thickness) [m]:
    D_chamber = D_in - 2 * liner_thickness
    # Defining 'grain' as an instance of BATES:
    grain = BATES(N, D_grain, D_core, L_grain)
    # Defining 'structure' as an instance of the MotorStructure class:
    structure = MotorStructure(
        sf, m_motor, D_in, D_out, D_chamber, L_chamber, D_screw, D_clearance, D_throat, get_circle_area(D_throat), C1,
        C2, Div_angle, Conv_angle, Exp_ratio, Y_chamber, Y_nozzle, Y_bulkhead, U_screw, max_number_of_screws
    )
    # Defining 'rocket' as an instance of Rocket class:
    rocket = Rocket(mass_wo_motor, Cd, D_rocket)
    # Defining 'recovery' as an instance of Recovery class:
    recovery = Recovery(drogue_time, Cd_drogue, D_drogue, Cd_main, D_main, main_chute_activation_height)

    ballistics, ib_parameters = run_ballistics(propellant, propellant_data, grain, structure, rocket, recovery, dt, ddt,
                                               h0, P_igniter, rail_length)

    plot = pressure_plot(ib_parameters.t, ib_parameters.P0, ib_parameters.t_burnout)

    print(np.max(ib_parameters.P0))

    return plot, np.max(ib_parameters.P0)


if __name__ == '__main__':
    app.run_server()
