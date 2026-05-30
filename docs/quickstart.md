# Quick Start

This guide shows how to simulate a Solid Rocket Motor with a BATES grain geometry using Machwave.

## 1. Choose a propellant

Machwave ships with several pre-defined solid propellant formulations.
Here we use KNDX (65% potassium nitrate and 35% dextrose):

```python
from machwave import formulations

propellant = formulations.solid.KNDX
```

For a full list of available solid propellants, see the
[formulations page](api/models/propellants/formulations.md).

## 2. Define the grain geometry

Create a `Grain` and add one or more segments.

```python
from machwave import grain as grain_models

grain = grain_models.Grain(spacing=10e-3)  # 10 mm spacing between segments

bates_segment = grain_models.geometries.BatesSegment(
    outer_diameter=41e-3,   # 41 mm
    core_diameter=15e-3,    # 15 mm
    length=67.5e-3,         # 67.5 mm
)

for _ in range(4):
    grain.add_segment(bates_segment)
```

## 3. Build the thrust chamber

The thrust chamber is composed of a **nozzle** and a **combustion chamber**:

```python
from machwave import thrust_chamber as thrust_chamber_models

nozzle = thrust_chamber_models.Nozzle(
    inlet_diameter=43e-3,
    throat_diameter=9.5e-3,
    divergent_angle=12,     # degrees
    convergent_angle=40,    # degrees
    expansion_ratio=8,
)

combustion_chamber = thrust_chamber_models.CombustionChamber(
    casing_inner_diameter=44.5e-3,
    casing_outer_diameter=50.8e-3,
    thermal_liner_thickness=1e-3,
    internal_length=grain.total_length + 10e-3,
)

thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
    dry_mass=0.85,          # kg
    nozzle=nozzle,
    combustion_chamber=combustion_chamber,
    nozzle_exit_to_grain_port_distance=0.01,
)
```

## 4. Assemble the motor

Combine the grain, propellant, and thrust chamber into a `SolidMotor`:

```python
from machwave import motors

motor = motors.SolidMotor(
    grain=grain,
    propellant=propellant,
    thrust_chamber=thrust_chamber,
)
```

## 5. Configure and run the simulation

Set up the simulation parameters and run it. `run()` returns a frozen
`SimulationResult` containing all ballistic time-series and derived metrics:

```python
from machwave import simulation

params = simulation.InternalBallisticsSimulationParams(
    d_t=0.01,                # time step [s]
    igniter_pressure=1e6,    # 1 MPa
    external_pressure=1e5,   # 1 atm
)

sim = simulation.InternalBallisticsSimulation(motor=motor, params=params)
result = sim.run()
```

## 6. View results

Print a summary of key performance metrics and plot the thrust and chamber
pressure curves:

```python
from machwave.services.plots import internal_ballistics as ib_plots

result.report()

ib_plots.thrust_pressure_plot(result.time, result.thrust, result.chamber_pressure).show()
```

`result.report()` outputs initial propellant mass, max/average chamber pressure,
burn time, max/average thrust, specific impulse, and total impulse.

For more complete examples, including coupled trajectory simulations and Monte
Carlo analyses, see the
[examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).
