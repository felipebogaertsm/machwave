<p align="center">
  <img src="assets/logo/machwave-lockup-color.svg#only-light" alt="Machwave" width="400">
  <img src="assets/logo/machwave-lockup-white.svg#only-dark" alt="Machwave" width="400">
</p>

Machwave is an open source Python library for **internal ballistics simulation** of chemical rocket propulsion systems.
Machwave's main capabilities are:

- **Propellant modeling** with pre-defined formulations, and NASA CEA integration
  for composition-derived thermochemistry
- **Grain regression analysis** with the fast marching method for 2D and 3D geometries
- **Motor/engine simulation** for the following categories:
    - Solid Rocket Motors
    - *Bipropellant Liquid Rocket Engines (in development 🔧)*
    - *Hybrid Rocket Engines (coming soon 🗓️)*
- **Monte Carlo simulation** for all of the motors/engines above
- **Integration with RocketPy** for trajectory simulation and analysis

## Installation

```bash
pip install machwave
```

The core install can run a complete solid rocket motor simulation with BATES grains, using any of the preset solid propellant formulations.
Additional capabilities, such as fast marching method grain regression, liquid feed system modeling or RocketPy trajectory simulation, can be unlocked by installing the optional extras:

| Extra | Unlocks |
| --- | --- |
| `cea` | Thermochemistry computed from propellant composition: every biliquid propellant, and solid formulations defined without pre-computed properties |
| `liquid` | Fluid state models for propellant tanks and injectors |
| `fmm` | Fast marching method grain regression, for every grain geometry other than BATES, including grains defined by an STL mesh |
| `plots` | The built-in figures and the Monte Carlo plots |
| `rocketpy` | The RocketPy adapter for trajectory simulation |
| `all` | All of the above |

Install one or several by name, for example:

```bash
pip install machwave[fmm,plots]
```

## Getting Started

The [Quick Start page](quickstart.md) covers a Solid Rocket Motor simulation.
For more complete examples, including coupled trajectory simulation with RocketPy and Monte Carlo, check out the [examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).

## License

Machwave is licensed under the [GNU General Public License v3.0](https://github.com/felipebogaertsm/machwave/blob/main/license.txt).
