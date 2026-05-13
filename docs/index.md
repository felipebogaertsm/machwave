# Machwave

Machwave is an open source Python library for chemical rocket propulsion simulation. The
library enables modeling and simulating solid rocket motors and bipropellant liquid
engines; hybrid engines are coming soon.

### Key Capabilities

- **Propellant modeling** with pre-defined formulations or CEA custom propellants
- **Propellant grain analysis** with FMM-based regression (BATES, star, finocyl, and
    more)
- **Solid rocket motor and bipropellant liquid engine modeling and simulation** (hybrid engines coming soon)
- **Monte Carlo simulation**
- **RocketPy trajectory simulation integration** (see [docs](api/adapters/rocketpy.md)
    for details)

## Why Machwave?

Machwave provides a programmatic interface for modeling chemical propulsion systems,
allowing users to have more control and flexibility over their designs and simulations.
Other tools may offer similar capabilities, but they often come with limitations such as
being closed source, lacking integration with trajectory simulations, or not being
flexible enough for more advanced users.


## Installation

Machwave requires **Python 3.11 – 3.14**.

```bash
pip install machwave
```

or, for the full integration with RocketPy:

```bash
pip install machwave[rocketpy]
```

## Quick Start

Start with the step-by-step walkthrough on the
[Quick Start page](quickstart.md), which covers propellant selection, grain
geometry, thrust chamber setup, simulation execution, and result plotting.

For more complete examples, including coupled trajectory simulations and Monte
Carlo analyses, see the
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
