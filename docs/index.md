# Machwave

Machwave is a Python library for chemical propulsion simulation. The library makes it
easy to model solid or liquid rocket engines, analyse performance and integrate the
results into trajectory simulations.

## Installation

```bash
pip install machwave
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
