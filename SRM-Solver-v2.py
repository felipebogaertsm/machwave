import time

from functions.InternalBallistics import *
from functions.Propellant import *
from functions.MotorStructure import *
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
m_motor = 15

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
structure = MotorStructure(
    sf, m_motor, D_in, D_out, D_chamber, L_chamber, D_screw, D_clearance, D_throat, get_circle_area(D_throat), C1, C2,
    Div_angle, Conv_angle, Y_chamber, Y_nozzle, Y_bulkhead, U_screw, max_number_of_screws
)

# _____________________________________________________________________________________________________________________
# INTERNAL BALLISTICS

ib_parameters = run_internal_ballistics(propellant_data, grain, structure, web_res, P_igniter, P_external, dt, propellant)

# _____________________________________________________________________________________________________________________
# MOTOR STRUCTURE

structural_parameters = run_structural_simulation(structure, ib_parameters)

# _____________________________________________________________________________________________________________________
# RESULTS

print_results(grain, structure, propellant_data, ib_parameters, structural_parameters)

# _____________________________________________________________________________________________________________________
# OUTPUT TO ENG AND CSV FILE

output_eng_csv(ib_parameters, structure, propellant_data, 25, dt, manufacturer, name)

# _____________________________________________________________________________________________________________________
# TIME FUNCTION END

print('Execution time: %.4f seconds\n\n' % (time.time() - start))

# _____________________________________________________________________________________________________________________
# PLOTS

performance_figure = performance_plot(ib_parameters.F, ib_parameters.P0, ib_parameters.t)
main_figure = main_plot(ib_parameters.t, ib_parameters.F, ib_parameters.P0, ib_parameters.Kn, ib_parameters.m_prop)
mass_flux_figure = mass_flux_plot(ib_parameters.t, ib_parameters.grain_mass_flux)
