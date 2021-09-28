# SRM Solver
## Written by: Felipe Bogaerts de Mattos
## Created on August, 2020

This program simulates the Internal Ballistics of a Solid Rocket Motor using a BATES grain geometry. The length and core
diameter can be input for each individual grain, guaranteeing more flexibility while designing an SRM. The list of
standard propellants and their specifications can be found inside the 'functions.py' file. Nozzle correction factors were
obtained from the a015140 paper.

# How to use (procedural, as a script):

As a quick demo of what this application can do, the procedural script performs a coupled internal and external ballistics simulation of a Solid Rocket Motor. This script's location is "srm_solver/SRM-Solver.py" and it is divided into several sections:

1) Time Function Start
2) Inputs
3) Pre Calculations
4) Internal Ballistics and Trajectory
5) Results
6) Output to .eng and .csv file
7) Time function end
8) Plots

Input the desired motor data inside the INPUTS section. Run the program and the main results will be displayed in the
Command Window. Inside the output folder created, a .eng and a .csv file will also be available with the important data
for a rocket ballistic simulation. Also, plots with the motor thrust, chamber pressure, Kn, propellant mass and mass
flux will be stored inside the same output folder.

Make sure all the modules are properly installed!

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

List of fully supported propellants:

- KNDX (Nakka burn rate data)
- KNSB-NAKKA (Nakka burn rate data) and KNSB (Magnus Gudnason burn rate data)
- KNSU (Nakka burn rate data)
- KNER (Magnus Gudnason burn rate data)

# How it works

## File structure

The "srm_solver/classes" folder contains access to all of the custom classes that the software makes use. These custom classes are used either to store input data, perform calculations or to store simulation output data, as is the case with "Ballistics" and "InternalBallistics" for example.

The "srm_solver/functions" folder stores all the independent functions, performing isentropic flow calculations, unit conversions, geometric calculations, *et cetera*.

The "srm_solver/simulations" folder is used to store functions that simulate a certain SRM model.

Finally, the folder "srm_solver/output" is only used to store the output files from the procedural version of the application. 

All of the files that comprise the web application are stored inside the main folder "srm_solver_web". 

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
