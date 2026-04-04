# Machwave

Machwave is an open source Python library for chemical rocket propulsion simulation. The
library enables modeling and simulating solid (liquid and hybrid coming soon) rocket
motors and engines.

## Why Machwave?

Machwave provides a programmatic interface for modeling chemical propulsion systems, 
allowing users to have more control and flexibility over their designs and simulations.
Other tools may offer similar capabilities, but they often come with limitations such as
being closed source, lacking integration with trajectory simulations, or not being
flexible enough for more advanced users.

### Key Capabilities

- **Solid rocket motor modeling** (liquid and hybrid coming soon)
- **Grain geometry analysis** with FMM-based regression (BATES, star, finocyl, and more)
- **Flexible propellant modeling** with pre-defined formulations
- **Internal ballistics simulation**
- **Coupled trajectory simulation**
- **Monte Carlo analysis**
- **RocketPy integration** via the optional `machwave[rocketpy]` extra

## Installation

Machwave requires **Python 3.11 – 3.14**.

```bash
pip install machwave
```

or, for the full integration with RocketPy:

```bash
pip install machwave[rocketpy]
```

## Quick Start: Simulating a Solid Rocket Motor

This walkthrough builds a simple BATES-grain SRM from scratch, runs an internal
ballistics simulation, and plots the results.

### 1. Choose a propellant

Machwave ships with several pre-defined solid propellant formulations. Here we
use KNDX (potassium nitrate / dextrose):

```python
from machwave.models.propellants.formulations import (
    solid as solid_propellants,
)

propellant = solid_propellants.KNDX
```

For a full list of available solid propellants, see the
[formulations page](https://felipebogaertsm.github.io/machwave/api/models/propulsion/propellants/formulations/).

### 2. Define the grain geometry

Create a `Grain` and add one or more segments.

```python
from machwave.models import grain as grain_models
from machwave.models.grain import geometries as grain_geometries

grain = grain_models.Grain(spacing=10e-3)  # 10 mm spacing between segments

bates_segment = grain_geometries.BatesSegment(
    outer_diameter=41e-3,   # 41 mm
    core_diameter=15e-3,    # 15 mm
    length=67.5e-3,         # 67.5 mm
)

for _ in range(4):
    grain.add_segment(bates_segment)
```

### 3. Build the thrust chamber

The thrust chamber is composed of a **nozzle** and a **combustion chamber**:

```python
from machwave.models import thrust_chamber as thrust_chamber_models

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

### 4. Assemble the motor

Combine the grain, propellant, and thrust chamber into a `SolidMotor`:

```python
from machwave.models import motors

motor = motors.SolidMotor(
    grain=grain,
    propellant=propellant,
    thrust_chamber=thrust_chamber,
)
```

### 5. Configure and run the simulation

Set up the simulation parameters and run it. `run()` returns a time array and a
state object containing all ballistic data:

```python
from machwave.simulations import internal_ballistics

params = internal_ballistics.InternalBallisticsParams(
    d_t=0.01,                # time step [s]
    igniter_pressure=1e6,    # 1 MPa
    external_pressure=1e5,   # 1 atm
)

simulation = internal_ballistics.InternalBallistics(motor=motor, params=params)
time, state = simulation.run()
```

### 6. View results

Print a summary of key performance metrics and plot the thrust and chamber
pressure curves:

```python
from machwave.services.plots import internal_ballistics as ib_plots

simulation.print_results()

ib_plots.thrust_pressure_plot(time, state.thrust, state.P_0).show()
```

`print_results()` outputs initial propellant mass, max/average chamber pressure,
burn time, max/average thrust, specific impulse, and total impulse.

---

For more complete examples - including coupled trajectory simulations and Monte
Carlo analyses - see the
[examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).


## Development Setup

If you're contributing to Machwave, you'll need [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
uv sync
```

## License

Machwave is licensed under the [GNU General Public License v3.0](https://github.com/felipebogaertsm/machwave/blob/main/license.txt).