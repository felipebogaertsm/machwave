# Quick Start

In this tutorial we will simulate a 3-segment BATES grain solid rocket motor.

## 1. Choose a propellant

Machwave ships with several pre-defined solid formulations.
We will use KNDX, 65% potassium nitrate and 35% dextrose:

```python
from machwave import formulations

propellant = formulations.solid.KNDX
```

## 2. Define the grain geometry

We stack three identical BATES segments, 10 mm apart:

```python
from machwave import grain as grain_models

grain = grain_models.Grain(spacing=10e-3)

bates_segment = grain_models.geometries.BatesSegment(
    outer_diameter=65e-3,
    core_diameter=22e-3,
    length=100e-3,
)

for _ in range(3):
    grain.add_segment(bates_segment)
```

## 3. Build the thrust chamber

Next comes the thrust chamber, composed of a **nozzle** and a **combustion chamber**:

```python
from machwave import thrust_chamber as thrust_chamber_models

nozzle = thrust_chamber_models.Nozzle(
    throat_diameter=14e-3,
    divergent_angle=12,
    expansion_ratio=8,
)

combustion_chamber = thrust_chamber_models.CombustionChamber(
    inner_diameter=65.85e-3,
    internal_length=grain.total_length + 10e-3,
)

thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
    nozzle=nozzle,
    combustion_chamber=combustion_chamber,
    nozzle_exit_to_grain_port_distance=1e-2,
)
```

`inner_diameter` is the chamber bore, measured inside the liner if there is one: a 69.85 mm casing with a 2 mm liner leaves a 65.85 mm bore, just wide enough for our 65 mm grain.
Inhibitors belong to the grain, so an inhibitor sleeve is not subtracted from the bore: its annulus counts as free chamber volume.

## 4. Assemble the motor

`SolidMotor` combines the grain, the propellant, and the thrust chamber:

```python
from machwave import motors

motor = motors.SolidMotor(
    grain=grain,
    propellant=propellant,
    thrust_chamber=thrust_chamber,
)
```

## 5. Run the simulation

Every simulation needs a set of input parameters defined in `InternalBallisticsSimulationParams`.
The timestep `d_t` needs to be small enough for the simulation to converge: usually 1 ms is a safe choice.
The igniter pressure is the initial chamber pressure.

```python
from machwave import simulation

params = simulation.InternalBallisticsSimulationParams(
    d_t=1e-3,
    igniter_pressure=1e6,
    external_pressure=1e5,
)

simulation = simulation.InternalBallisticsSimulation(motor=motor, params=params)
result = simulation.run()
```

`run()` marches through the burn and returns a frozen `SimulationResult`.

## 6. Read the results

We print the report and plot thrust against chamber pressure:

```python
from machwave.services.plots import internal_ballistics as ib_plots

result.report()

ib_plots.thrust_pressure_plot(result.time, result.thrust, result.chamber_pressure).show()
```

!!! note "The plot needs the `plots` extra"

```text
INTERNAL BALLISTICS SIMULATION RESULTS

BURN REGRESSION
 Propellant initial mass 1.647 kg
 Initial propellant volume: 881.452 cm^3
 Initial burn area: 383.636 cm^2
 Peak burn area: 432.896 cm^2
 Mean Kn: 264.71
 Max Kn: 281.21
 Initial to final Kn ratio: 1.098
 Volumetric efficiency: 78.430%
 Burn profile: regressive
 Max initial mass flux: 1758.430 kg/s-m-m or 2.501 lb/s-in-in

CHAMBER PRESSURE
 Maximum, average chamber pressure: 5.810, 4.778 MPa

THRUST AND IMPULSE
 Maximum, average thrust: 1290.482, 1049.092 N
 Total, specific impulses: 2037.248 N-s, 126.167 s
 Burnout time: 1.880 s, thrust time: 1.941 s

NOZZLE
  Average geometric throat area: 1.539 cm^2
  Average effective throat area: 1.539 cm^2
  Average nozzle efficiency: 86.745%
  Average divergent nozzle loss fraction: 1.093%
  Average kinetics loss fraction: 0.114%
  Average boundary layer loss fraction: 3.136%
  Average two-phase flow loss fraction: 3.921%
  Average other losses fraction: 5.000%
```

## Congratulations!

We have just simulated a solid rocket motor with Machwave.
The [examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples)
contains more complex use cases, including coupled trajectory with RocketPy and
Monte Carlo simulation.
