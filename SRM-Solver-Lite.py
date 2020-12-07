# October 2020, Felipe Bogaerts de Mattos
# All the measurements are in SI, unless specified otherwise in the variable comment above.

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
import streamlit as st
import plotly.graph_objects as go
import plotly.subplots
import fluids.atmosphere as atm

from functions.Simulation import *
from functions.Ballistics import *
from functions.InternalBallistics import *
from functions.Propellant import *
from functions.MotorStructure import *
from functions.functions import *

# ______________________________________________________________________________________________________________________
# INITIAL DEFINITIONS

prop_dict = {
    'KNDX (Nakka)': 'kndx',
    'KNSB (Nakka)': 'knsb-nakka',
    'KNSB (Gudnason)': 'knsb',
    'KNER (Gudnason)': 'kner'
}
prop_list = list(prop_dict.keys())
material_dict = {
    '6061-T6 Aluminum': '6061_t6',
    '1045 Steel': '1045_steel',
    '304 Stainless': '304_stainless'
}
material_list = list(material_dict.keys())
# Time step [s]:
dt = 1e-3
# Web regression resolution:
web_res = 1000

# _____________________________________________________________________________________________________________________
# STREAMLIT TITLE

st.title("SRM Solver")
st.write("""
### Simulate a BATES grain Solid Rocket Motors from your web browser
""")

# ______________________________________________________________________________________________________________________
# STREAMLIT SIDEBAR INPUTS

st.sidebar.header('Input section')
propellant = st.sidebar.selectbox('Select propellant', prop_list)
propellant = prop_dict[propellant]
N = st.sidebar.number_input('Grain count', min_value=1, max_value=20, step=1, value=4)
D_grain = st.sidebar.number_input('Grain external diameter [mm]',
                                  min_value=0.1, max_value=1000.0, value=41.0, step=0.5) * 1e-3
grain_spacing = st.sidebar.number_input('Grain spacing [mm]', max_value=D_grain * 1e3, value=5.0, step=1.0) * 1e-3
D_core, L_grain = np.zeros(N), np.zeros(N)
neutral_burn_profile = st.sidebar.checkbox('Neutral burn profile', value=True)
st.sidebar.write("""### Core diameter""")
single_core_diameter = st.sidebar.checkbox('Single core diameter', value=True)
if single_core_diameter:
    D_core = np.ones(N) * st.sidebar.number_input(f'Core diameter [mm]',
                                                  max_value=D_grain * 1e3, min_value=0.1, value=15.0, step=0.5) * 1e-3
else:
    for i in range(N):
        D_core[i] = st.sidebar.number_input(f'Core diameter #{i + 1} [mm]',
                                            max_value=D_grain * 1e3, min_value=0.1, value=15.0, step=0.5) * 1e-3
if neutral_burn_profile:
    for i in range(N):
        L_grain[i] = 0.5 * (3 * D_grain + D_core[i])
else:
    st.sidebar.write("""### Grain length""")
    for i in range(N):
        L_grain[i] = st.sidebar.number_input(f'Grain length #{i + 1} [mm]',
                                             value=0.5 * (3 * D_grain + D_core[i]) * 1e3, step=0.5) * 1e-3
st.sidebar.write("""### Combustion chamber""")
D_in = st.sidebar.number_input('Combustion chamber inside diameter [mm]',
                               min_value=0.1, step=0.05, value=43.0) * 1e-3
D_out = st.sidebar.number_input('Combustion chamber outer diameter [mm]',
                                min_value=D_in, max_value=1000.0, value=50.8)
liner_thickness = st.sidebar.number_input('Thermal liner thickness [mm]',
                                          min_value=0.1, step=0.25, value=0.725) * 1e-3
D_throat = st.sidebar.number_input('Throat diameter [mm]',
                                   min_value=0.1, max_value=D_in * 1e3, step=0.05, value=9.5) * 1e-3
Div_angle = st.sidebar.number_input('Divergent angle [deg]',
                                    min_value=0.0, max_value=60.0, value=12.0, step=2.0)
steel_nozzle = st.sidebar.checkbox('Steel nozzle', value=True)
P_igniter = st.sidebar.number_input('Igniter pressure [MPa]', min_value=0.1, step=0.5, value=1.5) * 1e6
P_external = st.sidebar.number_input('External pressure [MPa]', min_value=0.1, step=0.05, value=0.101325) * 1e6
st.sidebar.write("""### Structural design""")
nozzle_material = st.sidebar.selectbox('Nozzle material', material_list)
casing_material = st.sidebar.selectbox('Casing material', material_list)
bulkhead_material = st.sidebar.selectbox('Bulkhead material', material_list)
sf = st.sidebar.number_input('Safety factor',
                             min_value=1.5, max_value=10.0, step=0.5, value=4.0)
D_screw = st.sidebar.number_input('Screw diameter w/o threads [mm]',
                                  min_value=1.0, max_value=100.0, step=0.1, value=4.2) * 1e-3
D_clearance = st.sidebar.number_input('Screw clearance diameter [mm]',
                                      min_value=D_screw, max_value=100.0, step=0.1, value=5.0) * 1e-3
st.sidebar.write("""### Vehicle data""")
m_rocket = st.sidebar.number_input('Rocket mass w/o the motor [kg]',
                                   min_value=0.01, max_value=1000.0, step=0.1, value=2.8)
m_motor = st.sidebar.number_input('Motor structural mass [kg]',
                                  min_value=0.01, max_value=1000.0, step=0.01, value=0.85)
m_payload = st.sidebar.number_input('Payload mass [kg]',
                                    min_value=0.01, max_value=1000.0, step=0.01, value=0.8)
Cd = st.sidebar.number_input('Drag coefficient',
                             min_value=0.1, max_value=2.0, step=0.01, value=0.95)
D_rocket = st.sidebar.number_input('Rocket frontal diameter [mm]',
                                   min_value=10.0, max_value=1000.0, step=0.1, value=67.5) * 1e-3

# Initial height above sea level [m]
h0 = 4
# Launch rail length [m]
rain_length = 5
# Recovery data:
# Time after apogee for drogue parachute activation [s]
drogue_time = 1
# Drogue drag coefficient
Cd_drogue = 1.75
# Drogue effective diameter [m]
D_drogue = 1.25
# Main parachute drag coefficient [m]
Cd_main = 2
# Main parachute effective diameter [m]
D_main = 2.66
# Main parachute height activation [m]
main_chute_activation_height = 500

# ______________________________________________________________________________________________________________________
# PROPELLANT GRAIN DIMENSIONS

R_grain = D_grain / 2 * 1e3
R_core = D_core[0] / 2 * 1e3

plot_radial_grain = go.Figure(
    layout=go.Layout(
        title='Grain radial perspective',
        yaxis={'scaleanchor': 'x', 'scaleratio': 1, 'range': [- R_grain * 1.01, R_grain * 1.01]},
    )
)
plot_radial_grain.add_shape(
    type='circle',
    xref='x', yref='y',
    fillcolor='#dac36d',
    x0=- R_grain, x1=R_grain, y0=- R_grain, y1=R_grain
)
plot_radial_grain.add_shape(
    type='circle',
    xref='x', yref='y',
    fillcolor='#e3e3e3',
    x0=- R_core, x1=R_core, y0=- R_core, y1=R_core
)

st.write(' ### Propellant grain dimensions')
st.plotly_chart(plot_radial_grain)

# _____________________________________________________________________________________________________________________
# PRE CALCULATIONS AND DEFINITIONS

# The propellant name input above triggers the function inside 'Propellant.py' to return the required data.
ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
# Getting PropellantSelected class based on previous input:
propellant_data = PropellantSelected(
    ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex
)
# Combustion chamber length [m]:
L_chamber = np.sum(L_grain) + (N - 1) * grain_spacing
# Combustion chamber inner diameter (casing inner diameter minus liner thickness) [m]:
D_chamber = D_in - 2 * liner_thickness
# Defining 'grain' as an instance of BATES:
grain = BATES(web_res, N, D_grain, D_core, L_grain)
# Defining 'structure' as an instance of the MotorStructure class:
# structure = MotorStructure(
#     sf, m_motor, D_in, D_out, D_chamber, L_chamber, D_screw, D_clearance, D_throat, get_circle_area(D_throat), C1,
#     C2, Div_angle, Conv_angle, Exp_ratio, Y_chamber, Y_nozzle, Y_bulkhead, U_screw, max_number_of_screws
# )
# Defining 'rocket' as an instance of Rocket class:
rocket = Rocket(mass_wo_motor, Cd, D_rocket, structure)
# Defining 'recovery' as an instance of Recovery class:
recovery = Recovery(drogue_time, Cd_drogue, D_drogue, Cd_main, D_main, main_chute_activation_height)

# _____________________________________________________________________________________________________________________
# INTERNAL BALLISTICS AND TRAJECTORY

ballistics, ib_parameters = run_ballistics(propellant, propellant_data, grain, structure, rocket, recovery, dt, ddt, h0,
                                           P_igniter, rail_length)

# _____________________________________________________________________________________________________________________
# MOTOR STRUCTURE

structural_parameters = run_structural_simulation(structure, ib_parameters)

with st.beta_expander('Internal Ballistics'):
    st.plotly_chart(pressure_plot(ib_parameters.t, ib_parameters.P0))
    st.plotly_chart(thrust_plot(ib_parameters.t, ib_parameters.F))

# ______________________________________________________________________________________________________________________
# ROCKET BALLISTICS



# with st.beta_expander('1D Ballistics'):
#     st.plotly_chart(height_plot(t, y))
#     st.plotly_chart(velocity_plot(t, v))
