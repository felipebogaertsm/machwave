# Machwave

## Written by: Felipe Bogaerts de Mattos

## Created on August, 2020

Machwave is a Python package that helps engineers design rockets, rocket motors and rocket engines with efficiency and precision.

# Models and simulations

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

## Propellants

Propellant data was obtained from ProPEP3. This software has been used in several applications/projects and it is capable of delivering reliable information on the chemical characteristics of a specific propellant composition. Burn rate data is obtained from experiments conducted by Richard Nakka and Magnus Gudnason.

### Supported propellants

- KNDX (Nakka burn rate data)
- KNSB-NAKKA (Nakka burn rate data) and KNSB (Magnus Gudnason burn rate data)
- KNSU (Nakka burn rate data)
- KNER (Magnus Gudnason burn rate data)

# References

## a015140

Correction factors.

## Hans Seidel's Chamber Pressure article

Chamber Pressure equation.
