# Machwave

Machwave is an open source Python library for chemical propulsion simulation. The 
library enables easy modeling of solid (and liquid/hybrid in the near future) rocket 
engines, analyzing performance, and integrating the results into trajectory simulations.

## Why Machwave?

Machwave provides a programmatic interface for modeling chemical propulsion systems, 
allowing users to have more control and flexibility over their designs and simulations.
There are some other tools available on the internet for this type of simulation, but
they often come with limitations, such as being closed source, lacking easy integration
with trajectory simulations, or not being able to properly version control.

Machave:

- Is open source and free to use.
- Enables easy interation with internal and 3rd party trajectory simulation libraries.
- Allows for unlimited customization and control over the modeling process.
- Facilitates version control and collaboration through its programmatic interface.

## Installation

```bash
pip install machwave
```

or, for the full integration with RocketPy:

```bash
pip install machwave[rocketpy]
```

## Quick Example

```python
from machwave import simulations
from machwave.models.propulsion import motors
from machwave.models.propulsion.propellants.formulations import solid as solid_propellants

knsb_propellant = solid_propellants.KNSB
motor = motors.SolidMotor(
    grain=bates_grain,
    propellant=knsb_propellant,
    thrust_chamber=thrust_chamber,
)

sim = simulations.InternalBallisticsSimulation(motor=motor, params=params)
results = sim.run()
sim.print_results()
```

## Development Setup

If you're contributing to Machwave, you'll need [Poetry](https://python-poetry.org/) for dependency management.

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
poetry install
```
