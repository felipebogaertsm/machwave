# SRM Solver

## Written by: Felipe Bogaerts de Mattos

## Created on August, 2020

This program simulates the Internal Ballistics of a Solid Rocket Motor using a BATES grain geometry. The length and core
diameter can be input for each individual grain, guaranteeing more flexibility while designing an SRM. The list of
standard propellants and its specifications can be found inside the 'functions.py' file. Nozzle correction factors were
obtained from the a015140 paper.

No erosive burning correction has been written (yet).

### HOW TO USE:

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

The code was structured according to the following main sections:

1) Time Function Start
2) Inputs
3) Pre Calculations
4) Internal Ballistics and Trajectory
5) Results
6) Output to .eng and .csv file
7) Time function end
8) Plots
