<p align="center">
  <img src="assets/logo/machwave-lockup-color.png#only-light" alt="Machwave" width="400">
  <img src="assets/logo/machwave-lockup-white.png#only-dark" alt="Machwave" width="400">
</p>

Machwave is an open source Python library for chemical rocket propulsion simulation.
Here is what it is capable of:

- **Propellant modeling** with NASA CEA integration and pre-defined formulations
- **Grain regression analysis** with FMM for 2D and 3D geometries
- **Rocket motor and engine simulation** for the following categories:
    - Solid Rocket Motors
    - *Bi-propellant Liquid Rocket Engines (in development 🔧)*
    - *Hybrid Rocket Engines (coming soon 🗓️)*
- **Monte Carlo simulation** for all of the motors/engines above
- **Integration with RocketPy** for trajectory simulation and analysis

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

The [Quick Start page](quickstart.md) covers a Solid Rocket Motor simulation.
Propellant selection, grain geometry, nozzle design, simulation execution and result plotting.

For more complete examples, including coupled trajectory with RocketPy and Monte
Carlo simulation, check out the
[examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).

## License

Machwave is licensed under the [GNU General Public License v3.0](https://github.com/felipebogaertsm/machwave/blob/main/license.txt).
