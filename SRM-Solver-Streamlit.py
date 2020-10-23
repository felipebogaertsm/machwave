# October 2020, Felipe Bogaerts de Mattos
# All the measurements are in SI, unless specified otherwise in the variable comment above.

# IMPORT SECTION

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# INITIAL DEFINITIONS

prop_list = ['KNSB (Nakka)', 'KNSB (Gudnason)', 'KNER (Gudnason)', 'KNDX (Nakka)']

# STREAMLIT APP LAYOUT

st.title("SRM Solver")

st.write("""
### Simulate a BATES grain Solid Rocket Motors from your web browser
""")

# Sidebar:
propellant = st.sidebar.selectbox('Select propellant', prop_list)
N = st.sidebar.number_input('Grain count', min_value=1, max_value=20, step=1, value=4)
D_grain = st.sidebar.number_input('Grain external diameter [mm]',
                                  min_value=0.1, max_value=1000.0, value=41.0, step=0.05) * 1e-3
grain_spacing = st.sidebar.number_input('Grain spacing [mm]', max_value=D_grain * 1e3, value=5.0, step=1.0) * 1e-3
D_core, L_grain = np.zeros(N), np.zeros(N)
neutral_burn_profile = st.sidebar.checkbox('Neutral burn profile', value=True)
st.sidebar.write("""### Core diameter""")
for i in range(N):
    D_core[i] = st.sidebar.number_input(f'Core diameter #{i + 1} [mm]')
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
steel_nozzle = st.sidebar.checkbox('Steel nozzle', value=True)
P_igniter = st.sidebar.number_input('Igniter pressure [MPa]', min_value=0.1, step=0.5, value=1.5) * 1e6

