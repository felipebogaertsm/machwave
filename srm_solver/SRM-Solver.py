# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

# This is the main file to execute the program in script mode. The inputs must
# be hard coded and this file must be run inside an environment where all the
# modules listed in 'requirements.txt' are properly installed. The outputs can
# be seen inside the folder 'output'.

# SRM-Solver.py is divided into 9 sections:
# 1) Time function start;
# 2) Inputs;
# 3) Pre calculations and definitions;
# 4) Internal ballistics and trajectory;
# 5) Motor structure;
# 6) Results;
# 7) Output to eng and csv file;
# 8) Time function end;
# 9) Plots.

import time

from functions.structure import *
from functions.simulation import *
from functions.functions import *

# ______________________________________________________________________________
# TIME FUNCTION START
# Starts the timer.

start = time.time()

# ______________________________________________________________________________
# INPUTS
# This section must be used to enter all the inputs for the script mode to be
# executed.

# Motor name (NO SPACES):
name = 'SRM5K'
# Motor manufacturer (NO SPACES):
manufacturer = 'LCP'
# Motor structural mass [kg]:
m_motor = 21.013

# SIMULATION PARAMETERS INPUT
# .eng file resolution:
eng_res = 25
# Time step [s]:
dt = 1e-2
# In order to optimize the speed of the program, the time step entered above is
# multiplied by a factor 'ddt' after the propellant is finished burning and
# thrust produced is 0.
ddt = 10
# Minimal safety factor:
safety_factor = 4

# BATES PROPELLANT INPUT
# Grain count:
grain_count = 7
# Grain external diameter [m]:
grain_outer_diameter = 117e-3
# Grains 1 to 'grain_count' core diameter [m]:
grain_core_diameter = np.array([45, 45, 45, 45, 60, 60, 60]) * 1e-3
# Grains 1 to 'grain_count' length [m]:
grain_length = np.array([200, 200, 200, 200, 200, 200, 200]) * 1e-3
# Grain spacing (used to determine chamber length) [m]:
grain_spacing = 10e-3

# PROPELLANT CHARACTERISTICS INPUT
# Propellant name:
propellant = 'knsb-nakka'

# THRUST CHAMBER
# Casing inside diameter [m]:
casing_inner_diameter = 128.2e-3
# Chamber outside diameter [m]:
casing_outer_diameter = 141.3e-3
# Liner thickness [m]
liner_thickness = 3e-3
# Throat diameter [m]:
nozzle_throat_diameter = 37e-3
# Nozzle divergent and convergent angle [degrees]:
divergent_angle, convergent_angle = 12, 30
# Expansion ratio:
expansion_ratio = 8
# Nozzle materials heat properties 1 and 2 (page 87 of a015140):
C1 = 0.00506
C2 = 0.00000

# EXTERNAL CONDITIONS
# Igniter pressure [Pa]:
igniter_pressure = 1.5e6
# Elevation above mean sea level [m]:
initial_elevation_amsl = 645

# MECHANICAL DATA
# Chamber yield strength [Pa]:
casing_yield_strength = 192e6
# Bulkhead yield strength [Pa]:
bulkhead_yield_strength = 255e6
# Nozzle material yield strength [Pa]:
nozzle_yield_strength = 215e6

# FASTENER DATA
# Screw diameter (excluding threads) [m]:
screw_diameter = 6.75e-3
# Screw clearance hole diameter [m]:
screw_clearance_diameter = 8.5e-3
# Tensile strength of the screw [Pa]:
screw_ultimate_strength = 510e6
# Maximum number of fasteners:
max_number_of_screws = 30

# VEHICLE DATA
# Mass of the rocket without the motor [kg]:
mass_wo_motor = 28
# Rocket drag coefficient:
drag_coeff = 0.5
# Frontal diameter [m]:
rocket_outer_diameter = 170e-3
# Launch rail length [m]
rail_length = 5
# Time after apogee for drogue parachute activation [s]
drogue_time = 1
# Drogue drag coefficient
drag_coeff_drogue = 1.75
# Drogue effective diameter [m]
drogue_diameter = 1.25
# Main parachute drag coefficient [m]
drag_coeff_main = 2
# Main parachute effective diameter [m]
main_diameter = 2.66
# Main parachute height activation [m]
main_chute_activation_height = 500

# ______________________________________________________________________________
# PRE CALCULATIONS AND DEFINITIONS
# This section is responsible for creating all of the instances of classes that
# can be obtained from the input data.
# It includes instanced of the classes: PropellantSelected, BATES,
# MotorStructure, Rocket, Rocket and Recovery.
# It also does some small calculations of the chamber length and chamber
# diameter.

# The propellant name input above triggers the prop_data function inside
# 'Propellant.py' to return the required data.
propellant_data = prop_data(propellant)

# Defining 'grain' as an instance of 'BATES' class:
grain = BATES(grain_count, grain_outer_diameter, grain_core_diameter, grain_length)

# Defining 'structure' as an instance of the 'MotorStructure' class:
structure = MotorStructure(
    safety_factor,
    m_motor,
    casing_inner_diameter,
    casing_outer_diameter,
    screw_diameter,
    screw_clearance_diameter,
    nozzle_throat_diameter,
    C1,
    C2,
    divergent_angle,
    convergent_angle,
    expansion_ratio,
    casing_yield_strength,
    nozzle_yield_strength,
    bulkhead_yield_strength,
    screw_ultimate_strength,
    max_number_of_screws=max_number_of_screws,
)

# Defining 'rocket' as an instance of 'Rocket' class:
rocket = Rocket(mass_wo_motor, drag_coeff, rocket_outer_diameter)

# Defining 'recovery' as an instance of 'Recovery' class:
recovery = Recovery(
    drogue_time, drag_coeff_drogue, drogue_diameter, drag_coeff_main, main_diameter,
    main_chute_activation_height
)

# ______________________________________________________________________________
# INTERNAL BALLISTICS AND TRAJECTORY
# This section runs the main simulation of the program, returning the results
# of all the internal ballistics and trajectory calculations.
# The 'run_ballistics' function runs, in a single loop, the chamber pressure
# PDE as well as the rocket flight mechanics ODE.
# The exit pressure of the motor is automatically subtracted from the external
# (or ambient) pressure of the rocket during flight, yielding more precise
# motor thrust estimation.
# 'run_ballistics' returns instances of the classes Ballistics and
# InternalBallistics.

ballistics, ib_parameters = run_ballistics(
    propellant, propellant_data, grain, structure, rocket, recovery, dt, ddt,
    initial_elevation_amsl, igniter_pressure, rail_length
)

# ______________________________________________________________________________
# MOTOR STRUCTURE
# This section runs the structural simulation. The function
# 'run_structural_simulation' returns an instance of the class
# StructuralParameters.

structural_parameters = run_structural_simulation(structure, ib_parameters)

# ______________________________________________________________________________
# RESULTS
# This section prints the important data based on previous calculations.

print_results(
    grain, structure, propellant_data, ib_parameters, structural_parameters,
    ballistics
)

# ______________________________________________________________________________
# OUTPUT TO ENG AND CSV FILE
# This section exports the results inside a .csv and a .eng file. The .eng
# file is totally compatible with OpenRocket or RASAero software. The .csv is
# exported mainly for the ease of visualization and storage.

output_eng_csv(
    ib_parameters, structure, propellant_data, 25, dt, manufacturer, name
)

# ______________________________________________________________________________
# TIME FUNCTION END
# Ends the time function.

print('Execution time: %.4f seconds\n\n' % (time.time() - start))

# ______________________________________________________________________________
# PLOTS
# Saves some of the most important plots to the 'output' folder.

performance_figure = performance_plot(
    ib_parameters.T, ib_parameters.P0, ib_parameters.t, ib_parameters.t_thrust
)
main_figure = main_plot(
    ib_parameters.t, ib_parameters.T, ib_parameters.P0, ib_parameters.Kn,
    ib_parameters.m_prop, ib_parameters.t_thrust
)
mass_flux_figure = mass_flux_plot(
    ib_parameters.t, ib_parameters.grain_mass_flux, ib_parameters.t_thrust
)
ballistics_plots(ballistics.t, ballistics.acc, ballistics.v, ballistics.y, 9.81)
performance_interactive_plot(ib_parameters).show()
