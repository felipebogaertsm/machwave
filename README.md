# SRM Solver
## Written by: Felipe Bogaerts de Mattos
## Created on August, 2020

SRM Solver is an application that helps design Solid Rocket Motors. The main capability of this software is to perform a coupled simulation the internal and external ballistic of the motor/rocket. a BATES grain geometry.

THe software currently operated in two different modes, both as a web application and as a procedural script. The web application can be accessed through https://srmsolver.com and the procedural script can be executed following the rules contained in the next section.

# How to use (procedural, as a script):

As a quick demo of what this application can do, the procedural script performs a coupled internal and external ballistics simulation.

Pre-requisites: 

1. Having Python 3.6 or later installed on your machine.

Perform the actions below in order to perform the simulation with your own motor:

1. Change the data inside "srm_solver/motor_input.json". If there are any doubts regarding units or the format of such data, check the INPUTS section of "srm_solver/SRM-Solver.py";
1. Navigate to the Git repository folder using the terminal/command prompt;
1. Optional - enter your Python virtual environment;
1. Install the dependencies by running `pip install -r requirements.txt`;
1. Navigate into "srm_solver" directory;
1. Run `python SRM-Solver.py`.

The outputs from the procedural script can be seen inside `srm_solver/output`. After the script finished being executed, the results will also be printed into the terminal/command prompt window.

# How the application works

## Calculations and input parameters

Note that the grain #1 is the grain closest to the bulkhead and farthest from the nozzle.

The following assertions were taken into consideration:

- Propellant consisting of 2D BATES grain segments
- Cylindrical combustion chamber
- Thrust chamber composed of a simple flat end cap, conical nozzle and tubular casing
- Isentropic flow through nozzle
- Non-submerged nozzle
- Structure with screws as fasteners of both end cap and nozzle

Correction factors applied:

- Divergent CD nozzle angle
- Two phase flow
- Kinetic losses
- Boundary layer losses

## File structure

The "srm_solver/models" folder contains access to all of the custom classes that the software makes use. These custom classes are used either to store input data, perform calculations or to store simulation output data, as is the case with "Ballistics" and "InternalBallistics" for example.

The "srm_solver/utils" folder stores all the independent functions, performing isentropic flow calculations, unit conversions, geometric calculations, *et cetera*.

The "srm_solver/simulations" folder is used to store functions that simulate a certain SRM model.

Finally, the folder "srm_solver/output" is only used to store the output files from the procedural version of the application. 

All of the files that comprise the web application are stored inside the folder "srm_solver_web". 

## Propellant

The propellant data was obtained from ProPEP3. This software has been used in several applications/projects and it is capable of delivering reliable information on the chemical characteristics of a certain propellant composition.

### Supported propellants

In addition to the data fed by ProPEP3, it is necessary to gather the burn rate data as it changes with the chamber pressure. Burn rate data can only be obtained by experimentation, and for the purposes of this application, is sourced from a few reliable references on the internet.

The list of fully supported propellants is shown here:

- KNDX (Nakka burn rate data)
- KNSB-NAKKA (Nakka burn rate data) and KNSB (Magnus Gudnason burn rate data)
- KNSU (Nakka burn rate data)
- KNER (Magnus Gudnason burn rate data)

# Web Application (in progress)

The SRM Solver web app is being designed in order to make the process of designing and storing SRM models easier. The web application will be able to store user inputs in an organized manner inside a database, display simulation results and provide tools for designing better and more reliable motors. 

# References

## a015140

Correction factors.

## Hans Seidel's Chamber Pressure article

Chamber Pressure equation.
