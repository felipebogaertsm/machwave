# October 2020, Felipe Bogaerts de Mattos
# All the measurements are in SI, unless specified otherwise in the variable comment above.

# IMPORT SECTION

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
import streamlit as st
from functions.propellant import *
from functions.ib_functions import *

# INITIAL DEFINITIONS

prop_dict = {
    'KNSB (Nakka)': 'knsb-nakka',
    'KNSB (Gudnason)': 'knsb',
    'KNER (Gudnason)': 'kner',
    'KNDX (Nakka)': 'kndx'
}
prop_list = prop_dict.keys()
prop_list = ['KNSB (Nakka)', 'KNSB (Gudnason)', 'KNER (Gudnason)', 'KNDX (Nakka)']
# Time step [s]:
dt = 1e-3
# Web regression resolution:
web_res = 1000

# STREAMLIT TITLE

st.title("SRM Solver")

st.write("""
### Simulate a BATES grain Solid Rocket Motors from your web browser
""")

# STREAMLIT SIDEBAR

# Sidebar:
propellant = st.sidebar.selectbox('Select propellant', prop_list)
propellant = prop_dict[propellant]
N = st.sidebar.number_input('Grain count', min_value=1, max_value=20, step=1, value=4)
D_grain = st.sidebar.number_input('Grain external diameter [mm]',
                                  min_value=0.1, max_value=1000.0, value=41.0, step=0.05) * 1e-3
grain_spacing = st.sidebar.number_input('Grain spacing [mm]', max_value=D_grain * 1e3, value=5.0, step=1.0) * 1e-3
D_core, L_grain = np.zeros(N), np.zeros(N)
neutral_burn_profile = st.sidebar.checkbox('Neutral burn profile', value=True)
st.sidebar.write("""### Core diameter""")
for i in range(N):
    D_core[i] = st.sidebar.number_input(f'Core diameter #{i + 1} [mm]',
                                        max_value=D_grain * 1e3, min_value=0.1, value=15.0, step=0.5)
if neutral_burn_profile:
    for i in range(N):
        L_grain[i] = 0.5 * (3 * D_grain + D_core[i])
else:
    st.sidebar.write("""### Grain length""")
    for i in range(N):
        L_grain[i] = st.sidebar.number_input(f'Grain length #{i + 1} [mm]')
st.sidebar.write("""### Combustion chamber""")
D_in = st.sidebar.number_input('Combustion chamber inside diameter [mm]',
                               min_value=D_grain * 1e3, step=0.05, value=44.45) * 1e-3
D_throat = st.sidebar.number_input('Throat diameter [mm]',
                                   min_value=0.1, max_value=D_in * 1e3, step=0.05, value=9.5) * 1e-3
Div_angle = st.sidebar.number_input('Divergent angle [deg]',
                                    min_value=0.0, max_value=60.0, value=12.0, step=2.0)
steel_nozzle = st.sidebar.checkbox('Steel nozzle', value=True)
P_igniter = st.sidebar.number_input('Igniter pressure [MPa]', min_value=0.1, step=0.5, value=1.5) * 1e6
P_external = st.sidebar.number_input('External pressure [MPa]', min_value=0.1, step=0.5, value=0.101325) * 1e6

# CALCULATIONS

if steel_nozzle:
    C1 = 0.00506
    C2 = 0.00000

ce, pp, k_ch, k_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
R_ch, R_ex = scipy.constants.R / M_ch, scipy.constants.R / M_ex
T0 = ce * T0_ideal
A_throat = circle_area(D_throat)
L_cc = np.sum(L_grain) + (N - 1) * grain_spacing
grain = BATES(web_res, N, D_grain, D_core, L_grain)

w = grain.web()
gAb = np.zeros((N, web_res))
gVp = np.zeros((N, web_res))

for j in range(N):
    for i in range(web_res):
        gAb[j, i] = grain.burnArea(w[j, i], j)
        gVp[j, i] = grain.grainVolume(w[j, i], j)

D_core_min_index = grain.minCoreDiamIndex()

for j in range(N):
    gAb[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gAb[j, :], left=0, right=0)
    gVp[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gVp[j, :], left=0, right=0)

A_burn = gAb.sum(axis=0)
V_prop = gVp.sum(axis=0)

w = w[D_core_min_index, :]

A_core = np.array([])
for j in range(N):
    A_core = np.append(A_core, circle_area(D_core[j]))
A_port = A_core[-1]
initial_port_to_throat = A_port / A_throat
burn_profile = getBurnProfile(A_burn)
optimal_grain_length = grain.optimalLength()

V0, V_empty = chamber_volume(L_cc, D_in, V_prop)
critical_pressure_ratio = (2 / (k_ch + 1)) ** (k_ch / (k_ch - 1))
P0, x, t, time_burnout = np.array([P_igniter]), np.array([0]), np.array([0]), 0
r0, re, r = np.array([]), np.array([]), np.array([])

i = 0
while x[i] <= w[web_res - 1] or P0[i] >= P_external / critical_pressure_ratio:
    a, n = burn_rate_coefs(propellant, P0[i])
    if a < 0:
        exit()
    r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
    re = np.append(re, 0)
    r = np.append(r, r0[i] + re[i])
    dx = dt * r[i]
    x = np.append(x, x[i] + dx)
    t = np.append(t, t[i] + dt)
    A_burn_CP = np.interp(x, w, A_burn, left=0, right=0)
    V0_CP = np.interp(x, w, V0, right=V_empty)
    V_prop_CP = np.interp(x, w, V_prop, right=0)
    k1 = CP_Seidel(P0[i], P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_ch, R_ch, T0, r[i])
    k2 = CP_Seidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_ch, R_ch, T0, r[i])
    k3 = CP_Seidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_ch, R_ch, T0, r[i])
    k4 = CP_Seidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_ch, R_ch, T0, r[i])
    P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)
    if time_burnout == 0 and A_burn_CP[i] == 0:
        time_burnout = t[i]
    i = i + 1

grain_mass_flux = grain.massFluxPerGrain(r, pp, x)
index = np.size(P0)
Kn = A_burn_CP / A_throat
m_prop = V_prop_CP * pp
P0_avg = np.mean(P0)
P0_psi = P0 * 1.45e-4
P0_psi_avg = np.mean(P0_psi)
E = expansion_ratio(P_external, P0, k_ex, index, critical_pressure_ratio)
E_avg = np.mean(E)
n_div = 0.5 * (1 + np.cos(np.deg2rad(Div_angle)))
n_kin, n_tp, n_bl = operational_correction_factors(P0, P_external, P0_psi, Isp_frozen, Isp_shifting, E,
                                                   D_throat, qsi_ch, index, critical_pressure_ratio, C1,
                                                   C2, V0, M_ch, t)
n_cf = ((100 - (n_kin + n_bl + n_tp)) * n_div / 100)
Cf = thrust_coefficient(P0, P_external, k_ex, n_cf)
F = Cf * A_throat * P0
F_avg = np.mean(F)
Cf_avg = np.mean(Cf)
I_total, I_sp = impulse(F_avg, t, m_prop)

# PLOTS


