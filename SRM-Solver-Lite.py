# October 2020, Felipe Bogaerts de Mattos
# All the measurements are in SI, unless specified otherwise in the variable comment above.

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
import streamlit as st
import plotly.graph_objects as go
import plotly.subplots
import fluids.atmosphere as atm

from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
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
propellant = st.sidebar.selectbox('Select prop', prop_list)
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

# ______________________________________________________________________________________________________________________
# PRE CALCULATIONS AND DEFINITIONS

# The Propellant name input above triggers the function inside 'Propellant.py' to return the required data.
ce, pp, k_mix_ch, k_2ph_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
# Gas constant per molecular weight calculations:
R_ch, R_ex = scipy.constants.R / M_ch, scipy.constants.R / M_ex
# Real combustion temperature based on the ideal temp. and the combustion efficiency [K]:
T0 = ce * T0_ideal
# Nozzle throat area [m-m]:
A_throat = get_circle_area(D_throat)
# Combustion chamber length [m]:
L_chamber = np.sum(L_grain) + (N - 1) * grain_spacing
# Combustion chamber inner diameter (casing inner diameter minus liner thickness) [m]:
D_chamber = D_in - 2 * liner_thickness
# Defining 'grain' as an instance of BATES:
grain = BATES(web_res, N, D_grain, D_core, L_grain)
# Defining 'structure' as an instance of the MotorStructure class:
structure = MotorStructure(sf, m_motor, D_in, D_out, L_chamber, D_screw, D_clearance)

if steel_nozzle:
    C1 = 0.00506
    C2 = 0.0

# ______________________________________________________________________________________________________________________
# INTERNAL BALLISTICS

web = grain.get_web_array()

A_burn_segment = np.zeros((N, web_res))
V_propellant_segment = np.zeros((N, web_res))

for j in range(N):
    for i in range(web_res):
        A_burn_segment[j, i] = grain.get_burn_area(web[j, i], j)
        V_propellant_segment[j, i] = grain.get_propellant_volume(web[j, i], j)

D_core_min_index = grain.get_min_core_diameter_index()
for j in range(N):
    A_burn_segment[j, :] = np.interp(web[D_core_min_index, :], web[j, :],
                                     A_burn_segment[j, :], left=0, right=0)
    V_propellant_segment[j, :] = np.interp(web[D_core_min_index, :], web[j, :],
                                           V_propellant_segment[j, :], left=0, right=0)
A_burn = A_burn_segment.sum(axis=0)
V_prop = V_propellant_segment.sum(axis=0)

web = web[D_core_min_index, :]

A_core = np.array([])
for j in range(N):
    A_core = np.append(A_core, get_circle_area(D_core[j]))
A_port = A_core[-1]
initial_port_to_throat = A_port / A_throat
burn_profile = get_burn_profile(A_burn)
optimal_grain_length = grain.get_optimal_segment_length()

V0, V_empty = get_chamber_volume(L_chamber, D_chamber, V_prop)
critical_pressure_ratio = get_critical_pressure(k_mix_ch)

P0, x, t, t_burnout = np.array([P_igniter]), np.array([0]), np.array([0]), 0
r0, re, r = np.array([]), np.array([]), np.array([])

i = 0
while x[i] <= web[web_res - 1] or P0[i] >= P_external / critical_pressure_ratio:
    a, n = get_burn_rate_coefs(propellant, P0[i])
    if a < 0:
        exit()
    r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
    re = np.append(re, 0)
    r = np.append(r, r0[i] + re[i])
    dx = dt * r[i]
    x = np.append(x, x[i] + dx)
    t = np.append(t, t[i] + dt)
    A_burn_CP = np.interp(x, web, A_burn, left=0, right=0)
    V0_CP = np.interp(x, web, V0, right=V_empty)
    V_prop_CP = np.interp(x, web, V_prop, right=0)
    k1 = solve_cp_seidel(P0[i], P_external, A_burn_CP[i],
                         V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn_CP[i],
                         V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn_CP[i],
                         V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn_CP[i],
                         V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
    if t_burnout == 0 and A_burn_CP[i] == 0:
        t_burnout = t[i]

    i = i + 1

grain_mass_flux = grain.get_mass_flux_per_segment(r, pp, x)

index = np.size(P0)
Kn = A_burn_CP / A_throat
m_prop = V_prop_CP * pp

P0_avg = np.mean(P0)
P0_psi = P0 * 1.45e-4
P0_psi_avg = np.mean(P0_psi)

E = get_expansion_ratio(P_external, P0, k_2ph_ex, critical_pressure_ratio)
P_exit = get_exit_pressure(k_2ph_ex, E, P0)

n_div = 0.5 * (1 + np.cos(np.deg2rad(Div_angle)))
n_kin, n_tp, n_bl = get_operational_correction_factors(P0, P_external, P0_psi, Isp_frozen, Isp_shifting, E,
                                                       D_throat, qsi_ch, index, critical_pressure_ratio, C1,
                                                       C2, V0, M_ch, t)
n_cf = ((100 - (n_kin + n_bl + n_tp)) * n_div / 100)
Cf = get_thrust_coefficient(P0, P_external, P_exit, E, k_2ph_ex, n_cf)
F = Cf * A_throat * P0
I_total, I_sp = get_impulses(np.mean(F), t, m_prop)

with st.beta_expander('Internal Ballistics'):
    st.plotly_chart(pressure_plot(t, P0))
    st.plotly_chart(thrust_plot(t, F))

# ______________________________________________________________________________________________________________________
# ROCKET BALLISTICS

y, v, t_flight = np.array([0]), np.array([0]), np.array([0])
apogee = 0
apogee_time = - 1
main_time = 0
dt = 0.1
r = D_rocket / 2

i = 0
while y[i] >= 0 or t_flight[i] < 7:
    F_flight = np.interp(t_flight, t, F, left=0, right=0)
    m_prop_flight = np.interp(t_flight, t, m_prop, left=m_prop[0], right=0)
    if i == 0:
        acc = np.array([F_flight[0] * (m_rocket + m_payload + m_prop_flight[0] + m_motor) * 0])
    p_air = atm.ATMOSPHERE_1976(y[i] + h0).rho
    g = atm.ATMOSPHERE_1976.gravity(h0 + y[i])
    print(y[i], v[i], acc[i])
    print(m_prop_flight[i], i)
    M = m_rocket + m_payload + m_motor + m_prop_flight[i]
    if i == 0:
        Minitial = M
    if v[i] < 0 and y[i] <= main_chute_activation_height and m_prop_flight[i] == 0:
        if main_time == 0:
            main_time = t[i]
        Adrag = (np.pi * r ** 2) * Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue + \
                (np.pi * D_main ** 2) * 0.25 * Cd_main
    elif apogee_time >= 0 and t[i] >= apogee_time + drogue_time:
        Adrag = (np.pi * r ** 2) * Cd + (np.pi * D_drogue ** 2) * 0.25 * Cd_drogue
    else:
        Adrag = (np.pi * r ** 2) * Cd
    D = (Adrag * p_air) * 0.5
    k1, l1 = ballistics_ode(y[i], v[i], F_flight[i], D, M, g)
    k2, l2 = ballistics_ode(y[i] + 0.5 * k1 * dt, v[i] + 0.5 * l1 * dt, F_flight[i], D, M, g)
    k3, l3 = ballistics_ode(y[i] + 0.5 * k2 * dt, v[i] + 0.5 * l2 * dt, F_flight[i], D, M, g)
    k4, l4 = ballistics_ode(y[i] + 0.5 * k3 * dt, v[i] + 0.5 * l3 * dt, F_flight[i], D, M, g)
    y = np.append(y, y[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
    v = np.append(v, v[i] + (1 / 6) * (l1 + 2 * (l2 + l3) + l4) * dt)
    acc = np.append(acc, (1 / 6) * (l1 + 2 * (l2 + l3) + l4))
    t_flight = np.append(t, t_flight[i] + dt)
    if y[i + 1] <= y[i] and m_prop_flight[i] == 0 and apogee == 0:
        apogee = y[i]
        apogee_time = t_flight[np.where(y == apogee)]
    i = i + 1

if y[-1] < 0:
    y = np.delete(y, -1)
    v = np.delete(v, -1)
    acc = np.delete(acc, -1)
    t = np.delete(t, -1)

v_rail = v[np.where(y >= rain_length)]
v_rail = v_rail[0]
y_burnout = y[np.where(v == np.max(v))]

with st.beta_expander('1D Ballistics'):
    st.plotly_chart(height_plot(t, y))
    st.plotly_chart(velocity_plot(t, v))
