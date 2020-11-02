# SRM Solver
# Written by: Felipe Bogaerts de Mattos
# Created on August, 2020
# This program simulates the Internal Ballistics of a Solid Rocket Motor using a BATES grain geometry.
# The length and core diameter can be input for each individual grain, guaranteeing more flexibility while designing an
# SRM. The list of standard propellants and its specifications can be found inside the 'functions.py' file.
# Nozzle correction factors were obtained from the a015140 paper.
#
# No erosive burning correction has been written (yet).
#
# HOW TO USE:
# Input the desired motor data inside the INPUTS section. Run the program and the main results will be displayed in the
# Command Window. Inside the output folder created, a .eng and a .csv file will also be available with the important
# data for a rocket ballistic simulation. Also, plots with the motor thrust, chamber pressure, Kn, propellant mass and
# mass flux will be stored inside the same output folder.
#
# Make sure all the modules are properly installed!
#
# Note that the grain #1 is the grain closest to the bulkhead and farthest from the nozzle.
#
# The following assertions were taken into consideration:
# - Propellant consisting of 2D BATES grain segments
# - Cylindrical combustion chamber
# - Thrust chamber composed of a simple flat end cap, conical nozzle and tubular casing
# - Isentropic flow through nozzle
# - Non-submerged nozzle
# - Structure with screws as fasteners of both end cap and nozzle
#
# Correction factors applied:
# - Divergent CD nozzle angle
# - Two phase flow
# - Kinetic losses
# - Boundary layer losses
#
# List of fully supported propellants:
# - KNDX (Nakka burn rate data)
# - KNSB-NAKKA (Nakka burn rate data) and KNSB (Magnus Gudnason burn rate data)
# - KNSU (Nakka burn rate data)
# - KNER (Magnus Gudnason burn rate data)
#
# The code was structured according to the following main sections:
# 1) Time Function Start
# 2) Inputs
# 3) Pre Calculations
# 4) BATES Grain Calculations
# 5) Chamber Pressure RK4 Solver
# 6) Expansion Ratio and Exit Pressure
# 7) Motor Performance Losses
# 8) Thrust and Impulse
# 9) Motor Structure
# 10) Results
# 11) Output to .eng and .csv file
# 12) Time function End
# 13) Plots

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
import pandas as pd
import time
import json

from functions.ib_functions import *
from functions.propellant import *
from functions.structural_functions import *
from functions.functions import *

# _____________________________________________________________________________________________________________________
# TIME FUNCTION START

start = time.time()

# _____________________________________________________________________________________________________________________
# INPUTS

# Motor name (NO SPACES):
name = 'SRM5K'
# Motor manufacturer (NO SPACES):
manufacturer = 'LCP'
# Motor structural mass [kg]:
m_motor = 17

# SIMULATION PARAMETERS INPUT
# Web regression resolution:
web_res = 1000
# .eng file resolution:
eng_res = 25
# Time step [s]:
dt = 1e-3
# Minimal safety factor:
sf = 4

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
A_throat = getCircleArea(D_throat)

# Combustion chamber length [m]:
L_chamber = np.sum(L_grain) + (N - 1) * grain_spacing
# Combustion chamber inner diameter (casing inner diameter minus liner thickness) [m]:
D_chamber = D_in - 2 * liner_thickness

# Defining 'grain' as an instance of BATES:
grain = BATES(web_res, N, D_grain, D_core, L_grain)

# Defining 'structure' as an instance of the MotorStructure class:
structure = MotorStructure(sf, m_motor, D_in, D_out, L_chamber, D_screw, D_clearance)

# _____________________________________________________________________________________________________________________
# BATES GRAIN CALCULATION

# Creating a web distance array, for each grain:
w = grain.getWebArray()

# Pre-allocating the burn area and volume matrix for each grain segment. Rows are the grain segment number and columns
# are the burn area or volume value for each web regression step.
gAb = np.zeros((N, web_res))
gVp = np.zeros((N, web_res))

for j in range(N):
    for i in range(web_res):
        gAb[j, i] = grain.getBurnArea(w[j, i], j)
        gVp[j, i] = grain.getPropellantVolume(w[j, i], j)

# In case there are different initial core diameters or grain lengths, the for loop below interpolates all the burn
# area and Propellant volume data in respect to the largest web thickness of the motor.
# This ensures that that all grains ignite at the same time in the simulation and also that the distance between
# steps is equal for all grains in the matrix gAb and gVp.

D_core_min_index = grain.getMinCoreDiameterIndex()

for j in range(N):
    gAb[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gAb[j, :], left=0, right=0)
    gVp[j, :] = np.interp(w[D_core_min_index, :], w[j, :], gVp[j, :], left=0, right=0)

# Adding the columns of the matrices gAb and gVp to generate the vectors A_burn and V_prop, that contain the sum of
# the data for all grains in function of the web steps.
A_burn = gAb.sum(axis=0)
V_prop = gVp.sum(axis=0)

# Setting the web thickness matrix to the largest web thickness vector.
w = w[D_core_min_index, :]

# Core area:
A_core = np.array([])
for j in range(N):
    A_core = np.append(A_core, getCircleArea(D_core[j]))
# Port area:
A_port = A_core[-1]
# Port to throat area ratio:
initial_port_to_throat = A_port / A_throat

# Getting the burn profile
burn_profile = getBurnProfile(A_burn)
# Getting the optimal length for each grain segment
optimal_grain_length = grain.getOptimalSegmentLength()

# _____________________________________________________________________________________________________________________
# CHAMBER PRESSURE RK4 SOLVER

# Calculating the free chamber volume for each web step:
V0, V_empty = getChamberVolume(L_chamber, D_chamber, V_prop)

# Critical pressure (isentropic supersonic flow):
critical_pressure_ratio = (2 / (k_mix_ch + 1)) ** (k_mix_ch / (k_mix_ch - 1))

# Initial conditions:
P0, x, t, time_burnout = np.array([P_igniter]), np.array([0]), np.array([0]), 0
# Declaring arrays:
r0, re, r = np.array([]), np.array([]), np.array([])

# While loop iterates until the new instant web thickness vector 'x' is larger than the web thickness (last element of
# vector 'w') or the internal chamber pressure is smaller than critical pressure (making the nozzle exhaust subsonic).

i = 0

while x[i] <= w[web_res - 1] or P0[i] >= P_external / critical_pressure_ratio:

    # burn_rate_coefs selects value for a and n that suits the current chamber pressure of the iteration step.
    a, n = burn_rate_coefs(propellant, P0[i])

    # if 'a' and 'n' are negative, exit the program (lacking burn rate data for the current iteration of P0).
    if a < 0:
        exit()

    # The first time the while loop operates, the values for the burn rate are declared and written based on the
    # initial igniter pressure. 'r0' stands for the non-erosive burn rate term and 'r' stands for the total burn rate.
    # Currently, the program does not support erosive burning yet, o 'r0 = r'.
    # 'r0' is calculated using St. Robert's Burn Rate Law.
    r0 = np.append(r0, (a * (P0[i] * 1e-6) ** n) * 1e-3)
    re = np.append(re, 0)
    r = np.append(r, r0[i] + re[i])

    # The web distance that the combustion consumes on each time step 'dt' is represented by 'dx'.
    dx = dt * r[i]
    # The instant web distance vector is appended with latest 'dx' value.
    x = np.append(x, x[i] + dx)
    # The time vector 't' is also modified and the time step 'dt' is added to the last 't[i]' value.
    t = np.append(t, t[i] + dt)

    # In order for the burn area, chamber volume and Propellant volume vectors to be in function of time ('t') or in
    # function of web distance ('x') the old vectors 'A_burn', 'V0' and 'V_prop' must be interpolated from the old
    # set of web thickness data 'w' to the new vector 'x'.
    # A_burn_CP is the interpolated value for A_burn, in function of x and t;
    # V0_CP is the interpolated value for V0, in function of x and t;
    # V_prop_CP is the interpolated value for V_prop, in function of x and t.
    A_burn_CP = np.interp(x, w, A_burn, left=0, right=0)
    V0_CP = np.interp(x, w, V0, right=V_empty)
    V_prop_CP = np.interp(x, w, V_prop, right=0)

    # The values above are then used to solve the differential equation by the Range-Kutta 4th order method.
    k1 = solveCPSeidel(P0[i], P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k2 = solveCPSeidel(P0[i] + 0.5 * k1 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k3 = solveCPSeidel(P0[i] + 0.5 * k2 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])
    k4 = solveCPSeidel(P0[i] + 0.5 * k3 * dt, P_external, A_burn_CP[i], V0_CP[i], A_throat, pp, k_mix_ch, R_ch, T0, r[i])

    P0 = np.append(P0, P0[i] + (1 / 6) * (k1 + 2 * (k2 + k3) + k4) * dt)

    # 'time_burnout' stands for the time on which the Propellant is done burning. If the value for 'time_burnout'
    # (declared before the while loop) is 0 and the current iteration of 'AbCP' is also 0, time_burnout is set to the
    # current time value 't[i]'.
    if time_burnout == 0 and A_burn_CP[i] == 0:
        time_burnout = t[i]

    i = i + 1

# Mass flux per grain:
grain_mass_flux = grain.getMassFluxPerSegment(r, pp, x)

# The value for 'index' is used later to iterate on other useful vectors. I_total is set to the total length of the
# 'P0' vector in order to guarantee that future vectors will cover all the same instants that 'P0' covers.
index = np.size(P0)

# Klemmung in respect to time:
Kn = A_burn_CP / A_throat

# Propellant mass:
m_prop = V_prop_CP * pp

# Average value for the chamber pressure from ignition to the time when 'P0 <= critical_pressure_ratio':
P0_avg = np.mean(P0)

# Conversion of 'P0' from Pa to psi inside a new vector 'P0_psi'.
P0_psi = P0 * 1.45e-4
P0_psi_avg = np.mean(P0_psi)

# _____________________________________________________________________________________________________________________
# EXPANSION RATIO AND EXIT PRESSURE

E = getExpansionRatio(P_external, P0, k_2ph_ex, index, critical_pressure_ratio)
E = np.mean(E)

P_exit = getExitPressure(k_2ph_ex, E, P0)

# _____________________________________________________________________________________________________________________
# MOTOR PERFORMANCE LOSSES (a015140 paper)

n_div = 0.5 * (1 + np.cos(np.deg2rad(Div_angle)))

n_kin, n_tp, n_bl = getOperationalCorrectionFactors(P0, P_external, P0_psi, Isp_frozen, Isp_shifting, E,
                                                    D_throat, qsi_ch, index, critical_pressure_ratio, C1,
                                                    C2, V0, M_ch, t)

n_cf = ((100 - (n_kin + n_bl + n_tp)) * n_div / 100)

# _____________________________________________________________________________________________________________________
# THRUST AND IMPULSE

Cf = getThrustCoefficient(P0, P_external, P_exit, E, k_2ph_ex, n_cf)
F = Cf * A_throat * P0

F_avg = np.mean(F)
Cf_avg = np.mean(Cf)

I_total, I_sp = getImpulses(F_avg, t, m_prop)

# _____________________________________________________________________________________________________________________
# MOTOR STRUCTURE

# Casing thickness assuming thin wall [m]:
casing_sf = structure.casingSafetyFactor(Y_chamber, P0)

# Nozzle thickness assuming thin wall [m]:
nozzle_conv_t, nozzle_div_t, = structure.nozzleThickness(Y_nozzle, Div_angle, Conv_angle, P0)

# Bulkhead thickness [m]:
bulkhead_t = structure.bulkheadThickness(Y_bulkhead, P0)

# Screw safety factors and optimal quantity (shear, tear and compression):
optimal_fasteners, max_sf_fastener, shear_sf, tear_sf, compression_sf = \
    structure.optimalFasteners(max_number_of_screws, P0, Y_chamber, U_screw)

# _____________________________________________________________________________________________________________________
# RESULTS

print('\nResults generated by SRM Solver program, by Felipe Bogaerts de Mattos')

print('\nBURN REGRESSION')
if m_prop[0] > 1:
    print(f' Propellant initial mass {m_prop[0]:.3f} kg')
else:
    print(f' Propellant initial mass {m_prop[0] * 1e3:.3f} g')
print(' Mean Kn: %.2f' % np.mean(Kn))
print(' Initial to final Kn ratio: %.3f' % (A_burn[0] / A_burn[-1]))
print(f' Volumetric efficiency: {(V_prop_CP[0] * 100 / V_empty):.3f} %')
print(f' Grain length for neutral profile vector: {optimal_grain_length}')

print(' Burn profile: ' + burn_profile)
print(f' Initial port-to-throat (grain #{N:d}): {initial_port_to_throat:.3f}')
print(' Motor L/D ratio: %.3f' % (np.sum(L_grain) / D_grain))
print(f' Max initial mass flux: {np.max(grain_mass_flux):.3f} kg/s-m-m or '
      f'{np.max(grain_mass_flux) * 1.42233e-3:.3f} lb/s-in-in')

print('\nCHAMBER PRESSURE')
print(f' Maximum, average chamber pressure: {(np.max(P0) * 1e-6):.3f}, {(np.mean(P0) * 1e-6):.3f} MPa')

print('\nTHRUST AND IMPULSE')
print(f' Maximum, average thrust: {np.max(F):.3f}, {np.mean(F):.3f} N')
print(f' Total, specific getImpulses: {I_total:.3f} N-s, {I_sp:.3f} s')
print(f' Burnout time, thrust time: {time_burnout:.3f}, {t[-1]:.3f} s')

print('\nNOZZLE DESIGN')
print(f' Average opt. exp. ratio: {np.mean(E):.3f}')
print(f' Nozzle exit diameter: {D_throat * np.sqrt(np.mean(E)) * 1e3:.3f} mm')
print(f' Average nozzle efficiency: {np.mean(n_cf) * 100:.3f} %')

print('\nPRELIMINARY STRUCTURAL PROJECT')
print(f' Casing safety factor: {casing_sf:.2f}')
print(f' Minimal nozzle convergent, divergent thickness: {nozzle_conv_t * 1e3:.3f}, '
      f'{nozzle_div_t * 1e3:.3f} mm')
print(f' Minimal bulkhead thickness: {bulkhead_t * 1e3:.3f} mm')
print(f' Optimal number of screws: {optimal_fasteners + 1:d}')
print(f' Shear, tear, compression screw safety factors: {shear_sf[optimal_fasteners]:.3f}, '
      f'{tear_sf[optimal_fasteners]:.3f}, {compression_sf[optimal_fasteners]:.3f}')
print('\nDISCLAIMER: values above shall not be the final dimensions.')
print('Critical dimensions shall be investigated in depth in order to guarantee safety.')

print('\n')

# _____________________________________________________________________________________________________________________
# OUTPUT TO ENG AND CSV FILE
# This program exports the motor data into three separate files.
# The .eng file is compatible with most rocket ballistic simulators such as openRocket and RASAero.
# The output .csv file contains thrust, time, propellant mass, Kn, chamber pressure, web thickness and burn rate data.
# The input .csv file contains all info used in the input section.

# Forming a new time vector that has exactly 'eng_res' points (independent on time step input):
t_out = np.linspace(0, t[-1] + dt, eng_res)
# Interpolating old thrust-time data into new time vector:
F_out = np.interp(t_out, t, F, left=0, right=0)
# Interpolating the Propellant volume with the new time vector (to find prop. mass with t):
m_prop_out = pp * np.interp(t_out, t, V_prop_CP, right=0)

# Writing to the ENG file:
eng_header = f'{name} {D_out * 1e3:.4f} {L_chamber * 1e3:.4f} P ' \
             f'{m_prop_out[0]:.4f} {m_prop_out[0] + m_motor:.4f} {manufacturer}\n'
saveFile = open(f'output/{name}.eng', 'w')
saveFile.write('; Generated by SRM Solver program written by Felipe Bogaerts de Mattos\n; Juiz de Fora, Brasil\n')
saveFile.write(eng_header)
for i in range(eng_res):
    saveFile.write('   %.2f %.0f\n' % ((t_out[i]), (F_out[i])))
saveFile.write(';')
saveFile.close()

# Writing to output CSV file:
motor_data = {'Time': t, 'Thrust': F, 'Prop_Mass': m_prop, 'Chamber_Pressure': P0,
              'Klemmung': Kn, 'Web_Thickness': x}
motor_data_df = pd.DataFrame(motor_data)
motor_data_df.to_csv(f'output/{name}.csv', decimal='.')

# Writing the input CSV file:
motor_input = {'Name': name, 'Manufacturer': manufacturer, 'Motor Structural Mass': m_motor,
               'Grain Count': N, 'Grain Diam.': D_grain, 'Core Diam.': D_core,
               'Grain Length': L_grain, 'Propellant': propellant.upper(), 'Throat Diam.': D_throat,
               'Chamber Inside Diam.': D_in, 'Chamber Outside Diam.': D_out, 'Grain Spacing': grain_spacing,
               'Screw Diam.': D_screw, 'Clearance Diam.': D_clearance, 'Tensile Screw': U_screw,
               'Max. Number of Screws': max_number_of_screws, 'C1': C1, 'C2': C2,
               'Chamber Yield': Y_chamber, 'Bulkhead Yield': Y_bulkhead, 'Nozzle Yield': Y_nozzle,
               'Nozzle Convergent Angle': Conv_angle, 'Nozzle Divergent Angle': Div_angle,
               'External Temperature': T_external, 'External Pressure': P_external,
               'Igniter Pressure': P_igniter, 'Web Regression Res.': web_res, 'ENG File Res.': eng_res,
               'Time Step': dt, 'Minimal Safety Factor': sf}
motor_input_df = pd.DataFrame(motor_input)
motor_input_df.to_csv(f'output/{name}_input.csv', decimal='.')

# _____________________________________________________________________________________________________________________
# TIME FUNCTION END

print('Execution time: %.4f seconds\n\n' % (time.time() - start))

# _____________________________________________________________________________________________________________________
# PLOTS

plot_performance(F, P0, t)
plot_main(t, F, P0, Kn, m_prop)
plot_mass_flux(t, grain_mass_flux)
