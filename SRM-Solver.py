# Written by Felipe Bogaerts de Mattos
# Juiz de Fora, MG, 2020
# This is the main file to execute the program in script mode. The inputs must be hard coded and this file must be
# run inside an environment where all the modules listed in 'requirements.txt' are properly installed.
# The outputs can be seen inside the folder 'output' inside the project directory.
# SRM-Solver.py is divided into several sections:
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

from functions.MotorStructure import *
from functions.Simulation import *
from functions.functions import *

# _____________________________________________________________________________________________________________________
# TIME FUNCTION START
# Starts the timer.

start = time.time()

# _____________________________________________________________________________________________________________________
# INPUTS
# This section must be used to enter all the inputs for the script mode to be executed.

# Motor name (NO SPACES):
name = 'SRM5K'
# Motor manufacturer (NO SPACES):
manufacturer = 'LCP'
# Motor structural mass [kg]:
m_motor = 19.5

# SIMULATION PARAMETERS INPUT
# .eng file resolution:
eng_res = 25
# Time step [s]:
dt = 1e-2
# In order to optimize the speed of the program, the time step entered above is multiplied by a factor 'ddt' after the
# propellant is finished burning and thrust produced is 0.
ddt = 10
# Minimal safety factor:
sf = 4

# BATES PROPELLANT INPUT
# Grain count:
N = 7
# Grain external diameter [m]:
D_grain = 117e-3
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
D_in = 128.2e-3
# Chamber outside diameter [m]:
D_out = 141.3e-3
# Liner thickness [m]
liner_thickness = 3e-3
# Throat diameter [m]:
D_throat = 37e-3
# Nozzle divergent and convergent angle [degrees]:
Div_angle, Conv_angle = 12, 30
# Expansion ratio:
Exp_ratio = 8
# Nozzle materials heat properties 1 and 2 (page 87 of a015140):
C1 = 0.00506
C2 = 0.00000

# EXTERNAL CONDITIONS
# External temperature [K]:
T_external = 297
# Igniter pressure [Pa]:
P_igniter = 1.5e6
# Elevation [m]:
h0 = 645

# MECHANICAL DATA
# Chamber yield strength [Pa]:
Y_chamber = 192e6
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

# VEHICLE DATA
# Mass of the rocket without the motor [kg]:
mass_wo_motor = 30.5
# Rocket drag coefficient:
Cd = 0.5
# Frontal diameter [m]:
D_rocket = 170e-3
# Launch rail length [m]
rail_length = 5
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

# _____________________________________________________________________________________________________________________
# PRE CALCULATIONS AND DEFINITIONS
# This section is responsible for creating all of the instances of classes that can be obtained from the input data.
# It includes instanced of the classes: PropellantSelected, BATES, MotorStructure, Rocket, Rocket and Recovery.
# It also does some small calculations of the chamber length and chamber diameter.

# The propellant name input above triggers the function inside 'Propellant.py' to return the required data.
propellant_data = prop_data(propellant)
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

# _____________________________________________________________________________________________________________________
# INTERNAL BALLISTICS AND TRAJECTORY
# This section runs the main simulation of the program, returning the results of all the internal ballistics and
# trajectory calculations. The 'run_ballistics' function runs, in a single loop, the chamber pressure PDE as well as the
# rocket flight mechanics ODE. The exit pressure of the motor is automatically subtracted from the external (or ambient)
# pressure of the rocket during flight, yielding more precise motor thrust estimation.
# 'run_ballistics' returns instances of the classes Ballistics and InternalBallistics.

ballistics, ib_parameters = run_ballistics(propellant, propellant_data, grain, structure, rocket, recovery, dt, ddt, h0,
                                           P_igniter, rail_length)

# _____________________________________________________________________________________________________________________
# MOTOR STRUCTURE
# This section runs the structural simulation. The function 'run_structural_simulation' returns an instance of the class
# StructuralParameters.

structural_parameters = run_structural_simulation(structure, ib_parameters)

# _____________________________________________________________________________________________________________________
# RESULTS
# This section prints the important data based on previous calculations.

print_results(grain, structure, propellant_data, ib_parameters, structural_parameters, ballistics)

# _____________________________________________________________________________________________________________________
# OUTPUT TO ENG AND CSV FILE
# This section exports the results inside a .csv and a .eng file. The .eng file is totally compatible with OpenRocket or
# RASAero software. The .csv is exported mainly for the ease of visualization and storage.

output_eng_csv(ib_parameters, structure, propellant_data, 25, dt, manufacturer, name)

# _____________________________________________________________________________________________________________________
# TIME FUNCTION END
# Ends the time function.

print('Execution time: %.4f seconds\n\n' % (time.time() - start))

# _____________________________________________________________________________________________________________________
# PLOTS
# Saves some of the most important plots to the 'output' folder.

performance_figure = performance_plot(ib_parameters.T, ib_parameters.P0, ib_parameters.t, ib_parameters.t_thrust)
main_figure = main_plot(ib_parameters.t, ib_parameters.T, ib_parameters.P0, ib_parameters.Kn, ib_parameters.m_prop,
                        ib_parameters.t_thrust)
mass_flux_figure = mass_flux_plot(ib_parameters.t, ib_parameters.grain_mass_flux, ib_parameters.t_thrust)
ballistics_plots(ballistics.t, ballistics.acc, ballistics.v, ballistics.y, 9.81)
performance_interactive_plot(ib_parameters).show()
