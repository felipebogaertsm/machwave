import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from functions.ib_functions import *
from functions.structural_functions import *
from functions.propellant import *

app = dash.Dash(__name__)

# ________________________________________________________________________________
# INPUTS

# Motor name (NO SPACES):
name = 'NV3'
# Motor manufacturer (NO SPACES):
manufacturer = 'LP'
# Motor structural mass [kg]:
m_motor = 20

# SIMULATION PARAMETERS INPUT
# Web regression resolution:
web_res = 1000
# .eng file resolution
eng_res = 25
# Time step [s]
dt = 1e-3
# Minimal safety factor
sf = 4

# BATES PROPELLANT INPUT
# Grain count
N = 7
# Grain external diameter [m]
D_grain = 110e-3
# Grains 1 to 'N' core diameter [m]
D_core = np.array([40, 40, 40, 40, 40, 40, 40]) * 1e-3
# Grains 1 to 'N' length [m]
L_grain = np.array([185, 185, 185, 185, 185, 185, 185]) * 1e-3

# PROPELLANT CHARACTERISTICS INPUT
# Propellant name
propellant = 'kner'

# EXTERNAL CONDITIONS
# External temperature [K]
T_external = 297
# External pressure [Pa]
P_external = 0.101325e6
# Igniter pressure [Pa]
P_igniter = 2e6

# NOZZLE DIMENSIONS
# Throat diameter [m]
D_throat = 26e-3
# Nozzle material yield strength [Pa]
Y_nozzle = 215e6
# Nozzle divergent and convergent angle [degrees]
Div_angle, Conv_angle = 10, 30
# Nozzle materials heat properties 1 and 2 (page 87 of a015140)
C1 = 0.00506
C2 = 0.00000

# COMBUSTION CHAMBER
# Chamber inside diameter [m]
D_in = 127e-3
# Chamber outside diameter [m]
D_out = 139.7e-3
# Grain spacing [m]
grain_spacing = 15e-3
# Chamber yield strength [Pa]
Y_cc = 240e6
# Bulkhead yield strength [Pa]
Y_bulkhead = 255e6

# FASTENER DATA
# Screw diameter (excluding threads) [m]
D_screw = 6.75e-3
# Screw clearance hole diameter [m]
D_clearance = 8.5e-3
# Tensile strength of the screw [Pa]
U_screw = 510e6
# Maximum number of fasteners
max_number_of_screws = 30

# ______________________________________________________________
# PRE CALCULATIONS AND DEFINITIONS

# The Propellant name input above triggers the function inside 'Propellant.py' to return the required
# data.
ce, pp, k_ch, k_ex, T0_ideal, M_ch, M_ex, Isp_frozen, Isp_shifting, qsi_ch, qsi_ex = prop_data(propellant)
# Gas constant per molecular weight calculations
R_ch, R_ex = scipy.constants.R / M_ch, scipy.constants.R / M_ex
# Real combustion temperature based on the ideal temp. and the combustion efficiency [K]
T0 = ce * T0_ideal

# Nozzle throat area [m-m]
A_throat = circle_area(D_throat)

# Combustion chamber length [m]
L_cc = np.sum(L_grain) + (N - 1) * grain_spacing

# Defining 'grain' as an instance of BATES:
grain = BATES(web_res, N, D_grain, D_core, L_grain)

# Defining 'structure' as an instance of MotorStructure:
structure = MotorStructure(sf, m_motor, D_in, D_out, L_cc, D_screw, D_clearance)

# ______________________________________________________________
# BATES GRAIN CALCULATION

# Creating a web distance array, for each grain:
w = grain.web()

# Pre-allocating the burn area and volume matrix for each grain segment. Rows are the grain segment
# number and columns are the burn area or volume value for each web regression step.
gAb = np.zeros((N, web_res))
gVp = np.zeros((N, web_res))

for j in range(N):
    for i in range(web_res):
        gAb[j, i] = grain.burnArea(w[j, i], j)
        gVp[j, i] = grain.grainVolume(w[j, i], j)

# In case there are different initial core diameters or grain lengths, the for loop below interpolates
# all the burn area and Propellant volume data in respect to the largest web thickness of the motor.
# This ensures that that all grains ignite at the same time in the simulation and also that the
# distance between steps is equal for all grains in the matrix gAb and gVp.

D_core_min_index = grain.minCoreDiamIndex()

for j in range(N):
    gAb[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gAb[j, :], left=0, right=0)
    gVp[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gVp[j, :], left=0, right=0)

# Adding the columns of the matrices gAb and gVp to generate the vectors Ab and Vp, that contain
# the sum of the data for all grains in function of the web steps.
A_burn = gAb.sum(axis=0)
V_prop = gVp.sum(axis=0)

# Setting the web thickness matrix to the largest web thickness vector.
w = w[D_core_min_index, :]

# Core area:
A_core = np.array([])
for j in range(N):
    A_core = np.append(A_core, circle_area(D_core[j]))
# Port area:
A_port = A_core[-1]
# Port to throat area ratio (grain #1):
initial_port_to_throat = A_port / A_throat

# Getting the burn profile
burn_profile = getBurnProfile(A_burn)
# Getting the optimal length for each grain segment
optimal_grain_length = grain.optimalLength()

# ________________________________________________________________________________
# APP LAYOUT


