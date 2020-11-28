import numpy as np
import plotly.graph_objects as go

from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
from functions.functions import *

# _____________________________________________________________________________________________________________________
# INPUTS

# Motor name (NO SPACES):
name = 'SRM5K'
# Motor manufacturer (NO SPACES):
manufacturer = 'LCP'
# Motor structural mass [kg]:
m_motor = 17

# SIMULATION PARAMETERS INPUT
# .eng file resolution:
eng_res = 25
# Web step [m]:
dt = 1e-4

# BATES PROPELLANT INPUT
# Grain count:
N = 7
# Grain external diameter [m]:
D_grain = 114e-3
# Grains 1 to 'N' core diameter [m]:
D_core = np.array([45, 45, 45, 45, 60, 60, 60]) * 1e-3
# Grains 1 to 'N' length [m]:
L_grain = np.array([200, 200, 200, 200, 200, 200, 200]) * 1e-3
# Grain spacing (used to determine chamber length) [m]:
grain_spacing = 10e-3

# PROPELLANT CHARACTERISTICS INPUT
# Propellant name:
propellant = 'knsb-nakka'

# THRUST CHAMBER
# Casing inside diameter [m]:
D_in = 127e-3
# Chamber outside diameter [m]:
D_out = 139.7e-3
# Liner thickness [m]
liner_thickness = 3e-3
# Throat diameter [m]:
D_throat = 36e-3
# Nozzle divergent and convergent angle [degrees]:
Div_angle, Conv_angle = 12, 30
# Nozzle materials heat properties 1 and 2 (page 87 of a015140):
C1 = 0.00506
C2 = 0.00000

# EXTERNAL CONDITIONS
# External temperature [K]:
T_external = 297
# External pressure [Pa]:
P_external = 0.101325e6
# Igniter pressure [Pa]:
P_igniter = 1.5e6

# MECHANICAL DATA
# Chamber yield strength [Pa]:
Y_chamber = 240e6
# Bulkhead yield strength [Pa]:
Y_bulkhead = 255e6
# Nozzle material yield strength [Pa]:
Y_nozzle = 215e6

# FASTENER DATA
# Screw diameter (excluding threads) [m]:
D_screw = 6.75e-3
# Screw clearance hole diameter [m]:
D_clearance = 8.5e-3
# Tensile strength of the screw [Pa]:
U_screw = 510e6
# Maximum number of fasteners:
max_number_of_screws = 30

# _____________________________________________________________________________________________________________________
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
grain = BATES(1000, N, D_grain, D_core, L_grain)

# Defining 'structure' as an instance of the MotorStructure class:
structure = MotorStructure(4, m_motor, D_in, D_out, L_chamber, D_screw, D_clearance)

critical_pressure_ratio = get_critical_pressure(k_mix_ch)

# _____________________________________________________________________________________________________________________
# MAIN LOOP

A_burn_initial, V_propellant_initial = 0, 0
for n in range(N):
	A_burn_initial = A_burn_initial + grain.get_burn_area(0, n)
	V_propellant_initial = V_propellant_initial + grain.get_propellant_volume(0, n)

A_burn = np.array([A_burn_initial])
V_propellant = np.array([V_propellant_initial])
x = np.array([0])
t = np.array([0])
P0 = np.array([P_igniter])
r0 = np.array([])
V0 = np.array([np.pi * (D_chamber / 2) ** 2 * L_chamber - V_propellant_initial])

i = 0

while A_burn[i] > 0 or P0[i] >= critical_pressure_ratio * P_igniter:
	a, n = burn_rate_coefs(propellant, P0[i])
    r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
    dt = dx / r0[i]
    x = np.append(x, x[i] + dx)
    t = np.append(t, t[i] + dt)

    for n in range(N):
        A_burn_instant = A_burn_instant + grain.get_burn_area(x[i], n)
        V_propellant_instant = V_propellant_instant + grain.get_propellant_volume(x[i], n)

    A_burn, V_propellant = np.append(A_burn, A_burn_instant), np.append(V_propellant, V_propellant_instant)
    V0 = np.append(V0, np.pi * (D_chamber / 2) ** 2 * L_chamber - V_propellant[i])

    k1 = solve_cp_seidel(P0[i], P_external, A_burn[i],
                         V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k2 = solve_cp_seidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn[i],
                         V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k3 = solve_cp_seidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn[i],
                         V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k4 = solve_cp_seidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn[i],
                         V0[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])

    P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)

    i = i + 1

