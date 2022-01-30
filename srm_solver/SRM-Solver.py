# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
This is the main file to execute the program in script mode. The inputs must
be hard coded and this file must be run inside an environment where all the
modules listed in 'requirements.txt' are properly installed. The outputs can
be seen inside the folder 'output'.

SRM-Solver.py is divided into 9 sections:
1) Time function start;
2) Inputs;
3) Pre calculations and definitions;
4) Internal ballistics and trajectory;
5) Motor structure;
6) Results;
7) Output to eng and csv file;
8) Time function end;
9) Plots.
"""

import time
import numpy as np
import json
from pathlib import Path

from models.bates import Bates as BATES
from models.motor_structure import MotorStructure
from models.propellant import prop_data
from models.recovery import Recovery
from models.rocket import Rocket

from utils.utilities import output_eng_csv, print_results
from utils.plots import (
    performance_interactive_plot,
    performance_plot,
    main_plot,
    mass_flux_plot,
    ballistics_plots,
)

from simulations.internal_balistics_coupled import run_ballistics
from simulations.structural import run_structural_simulation

# /////////////////////////////////////////////////////////////////////////////
# TIME FUNCTION START
# Starts the timer.

start = time.time()

# /////////////////////////////////////////////////////////////////////////////
# INPUTS
# This section must be used to enter all the inputs for the script mode to be
# executed.

with open(Path("motor_input.json")) as motor_input:
    data = json.load(motor_input)

# Motor name (NO SPACES):
name = data["motor"]["name"]
# Motor manufacturer (NO SPACES):
manufacturer = data["motor"]["manufacturer"]
# Motor structural mass [kg]:
motor_structural_mass = data["structure"]["mass"]

# SIMULATION PARAMETERS INPUT
# .eng file resolution:
eng_res = data["simulationSettings"]["engResolution"]
# Time step [s]:
d_t = data["simulationSettings"]["dt"]
# In order to optimize the speed of the program, the time step entered above is
# multiplied by a factor 'dd_t' after the propellant is finished burning and
# thrust produced is 0.
dd_t = data["simulationSettings"]["ddt"]
# Minimal safety factor:
safety_factor = data["structure"]["safetyFactor"]

# BATES PROPELLANT INPUT
# Grain count:
segment_count = data["grain"]["count"]
# Grain external diameter [m]:
grain_outer_diameter = data["grain"]["outerDiameter"]
# Grains 1 to 'segment_count' core diameter [m]:
grain_core_diameter = np.array(data["grain"]["coreDiameter"])
# Grains 1 to 'segment_count' length [m]:
segment_length = np.array(data["grain"]["length"])
# Grain spacing (used to determine chamber length) [m]:
grain_spacing = data["grain"]["spacing"]

# PROPELLANT CHARACTERISTICS INPUT
# Propellant name:
propellant = data["propellant"]["name"]

# THRUST CHAMBER
# Casing inside diameter [m]:
casing_inner_diameter = data["structure"]["casingInnerDiameter"]
# Chamber outside diameter [m]:
casing_outer_diameter = data["structure"]["casingOuterDiameter"]
# Liner thickness [m]
liner_thickness = data["structure"]["linerThickness"]
# Throat diameter [m]:
nozzle_throat_diameter = data["structure"]["nozzleThroatDiameter"]
# Nozzle divergent and convergent angle [degrees]:
divergent_angle = data["structure"]["nozzleDivergentAngle"]
convergent_angle = data["structure"]["nozzleConvergentAngle"]
# Expansion ratio:
expansion_ratio = data["structure"]["expansionRatio"]
# Nozzle materials heat properties 1 and 2 (page 87 of a015140):
C1 = data["structure"]["casingC1"]
C2 = data["structure"]["casingC2"]

# EXTERNAL CONDITIONS
# Igniter pressure [Pa]:
igniter_pressure = data["simulationSettings"]["igniterPressure"]
# Elevation above mean sea level [m]:
initial_elevation_amsl = data["simulationSettings"]["initialAmslElevation"]

# MECHANICAL DATA
# Chamber yield strength [Pa]:
casing_yield_strength = data["structure"]["casingYieldStrength"]
# Bulkhead yield strength [Pa]:
bulkhead_yield_strength = data["structure"]["bulkheadYieldStrength"]
# Nozzle material yield strength [Pa]:
nozzle_yield_strength = data["structure"]["nozzleYieldStrength"]

# FASTENER DATA
# Screw diameter (excluding threads) [m]:
screw_diameter = data["structure"]["screwDiameter"]
# Screw clearance hole diameter [m]:
screw_clearance_diameter = data["structure"]["screwClearanceDiameter"]
# Tensile strength of the screw [Pa]:
screw_ultimate_strength = data["structure"]["screwUltimateStrength"]
# Maximum number of fasteners:
max_number_of_screws = data["structure"]["maxScrewCount"]

# VEHICLE DATA
# Mass of the rocket without the motor [kg]:
mass_wo_motor = data["rocket"]["massWithoutMotor"]
# Rocket drag coefficient:
drag_coeff = data["rocket"]["dragCoeff"]
# Frontal diameter [m]:
rocket_outer_diameter = data["rocket"]["outerDiameter"]
# Launch rail length [m]
rail_length = data["simulationSettings"]["railLength"]
# Time after apogee for drogue parachute activation [s]
drogue_time = data["recovery"]["drogueTime"]
# Drogue drag coefficient
drag_coeff_drogue = data["recovery"]["drogueDragCoeff"]
# Drogue effective diameter [m]
drogue_diameter = data["recovery"]["drogueDiameter"]
# Main parachute drag coefficient [m]
drag_coeff_main = data["recovery"]["mainDragCoeff"]
# Main parachute effective diameter [m]
main_diameter = data["recovery"]["mainDiameter"]
# Main parachute height activation [m]
main_chute_activation_height = data["recovery"]["mainActivationHeight"]

# /////////////////////////////////////////////////////////////////////////////
# PRE CALCULATIONS AND DEFINITIONS
# This section is responsible for creating all of the instances of classes that
# can be obtained from the input data.
# It includes instanced of the classes: PropellantSelected, BATES,
# MotorStructure, Rocket, Rocket and Recovery.
# It also does some small calculations of the chamber length and chamber
# diameter.

# The propellant name input above triggers the prop_data function inside
# 'Propellant.py' to return the required data.
propellant_data = prop_data(prop_name=propellant)

# Defining 'grain' as an instance of 'BATES' class:
grain = BATES(
    segment_count=segment_count,
    outer_diameter=grain_outer_diameter,
    core_diameter=grain_core_diameter,
    segment_length=segment_length,
)

# Defining 'structure' as an instance of the 'MotorStructure' class:
structure = MotorStructure(
    safety_factor=safety_factor,
    motor_structural_mass=motor_structural_mass,
    chamber_length=np.sum(segment_length)
    + (segment_count - 1) * grain_spacing,
    chamber_inner_diameter=casing_inner_diameter - 2 * liner_thickness,
    casing_inner_diameter=casing_inner_diameter,
    casing_outer_diameter=casing_outer_diameter,
    screw_diameter=screw_diameter,
    screw_clearance_diameter=screw_clearance_diameter,
    nozzle_throat_diameter=nozzle_throat_diameter,
    C1=C1,
    C2=C2,
    divergent_angle=divergent_angle,
    convergent_angle=convergent_angle,
    expansion_ratio=expansion_ratio,
    casing_yield_strength=casing_yield_strength,
    nozzle_yield_strength=nozzle_yield_strength,
    bulkhead_yield_strength=bulkhead_yield_strength,
    screw_ultimate_strength=screw_ultimate_strength,
    max_number_of_screws=max_number_of_screws,
)

# Defining 'rocket' as an instance of 'Rocket' class:
rocket = Rocket(
    mass_wo_motor=mass_wo_motor,
    drag_coeff=drag_coeff,
    outer_diameter=rocket_outer_diameter,
)

# Defining 'recovery' as an instance of 'Recovery' class:
recovery = Recovery(
    drogue_time=drogue_time,
    drag_coeff_drogue=drag_coeff_drogue,
    drogue_diameter=drogue_diameter,
    drag_coeff_main=drag_coeff_main,
    main_diameter=main_diameter,
    main_chute_activation_height=main_chute_activation_height,
)

# /////////////////////////////////////////////////////////////////////////////
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
    prop=propellant,
    propellant=propellant_data,
    grain=grain,
    structure=structure,
    rocket=rocket,
    recovery=recovery,
    d_t=d_t,
    dd_t=dd_t,
    initial_elevation_amsl=initial_elevation_amsl,
    igniter_pressure=igniter_pressure,
    rail_length=rail_length,
)

# /////////////////////////////////////////////////////////////////////////////
# MOTOR STRUCTURE
# This section runs the structural simulation. The function
# 'run_structural_simulation' returns an instance of the class
# StructuralParameters.

structural_parameters = run_structural_simulation(structure, ib_parameters)

# /////////////////////////////////////////////////////////////////////////////
# RESULTS
# This section prints the important data based on previous calculations.

print_results(
    grain,
    structure,
    ib_parameters,
    structural_parameters,
    ballistics,
    rocket,
)

# /////////////////////////////////////////////////////////////////////////////
# OUTPUT TO ENG AND CSV FILE
# This section exports the results inside a .csv and a .eng file. The .eng
# file is totally compatible with OpenRocket or RASAero software. The .csv is
# exported mainly for the ease of visualization and storage.

output_eng_csv(
    ib_parameters,
    structure,
    propellant_data,
    25,
    d_t,
    manufacturer,
    name,
)

# /////////////////////////////////////////////////////////////////////////////
# TIME FUNCTION END
# Ends the time function.

print("Execution time: %.4f seconds\n\n" % (time.time() - start))

# /////////////////////////////////////////////////////////////////////////////
# PLOTS
# Saves some of the most important plots to the 'output' folder.

performance_figure = performance_plot(
    ib_parameters.T, ib_parameters.P0, ib_parameters.t, ib_parameters.t_thrust
)
main_figure = main_plot(
    ib_parameters.t,
    ib_parameters.T,
    ib_parameters.P0,
    ib_parameters.Kn,
    ib_parameters.m_prop,
    ib_parameters.t_thrust,
)
mass_flux_figure = mass_flux_plot(
    ib_parameters.t, ib_parameters.grain_mass_flux, ib_parameters.t_thrust
)
ballistics_plots(
    ballistics.t, ballistics.acc, ballistics.v, ballistics.y, 9.81
)
performance_interactive_plot(ib_parameters).show()
