<p align="center">
  <img src="assets/logo/machwave-lockup-color.svg#only-light" alt="Machwave" width="400">
  <img src="assets/logo/machwave-lockup-white.svg#only-dark" alt="Machwave" width="400">
</p>

Machwave is an open source Python library for chemical rocket propulsion simulation.
Machwave's main capabilities are:

- **Propellant modeling** with pre-defined formulations, and NASA CEA integration
  for composition-derived thermochemistry (`cea` extra)
- **Grain regression analysis** with FMM for 2D and 3D geometries (`fmm` extra)
- **Rocket motor and engine simulation** for the following categories:
    - Solid Rocket Motors
    - *Bi-propellant Liquid Rocket Engines (in development 🔧)* (`cea` and `liquid` extras)
    - *Hybrid Rocket Engines (coming soon 🗓️)*
- **Monte Carlo simulation** for all of the motors/engines above
- **Integration with RocketPy** for trajectory simulation and analysis (`rocketpy` extra)

## Installation

Machwave requires **Python 3.11 – 3.14**.

```bash
pip install machwave
```

The core install depends only on NumPy, SciPy and fluids, and runs a complete solid
rocket motor simulation with BATES grains, any of the eight bundled solid propellant
formulations and the full Solid Performance Program 1975 nozzle loss set. Those
formulations carry pre-computed thermochemical properties, so no thermochemistry
solver is needed to burn them.

Everything heavier is an optional extra:

| Extra | Unlocks |
| --- | --- |
| `cea` | Thermochemistry computed from propellant composition, needed for biliquid engines and for custom solid mixtures |
| `liquid` | Propellant tanks and the injector's homogeneous-equilibrium mass flux |
| `fmm` | Every grain geometry other than BATES, including grains defined by an STL mesh |
| `plots` | The built-in figures and the Monte Carlo plots |
| `rocketpy` | The RocketPy adapter for trajectory simulation |
| `all` | All of the above |

Install one or several by name, for example:

```bash
pip install machwave[fmm,plots]
```

Using a feature without its extra raises an `ImportError` naming the install command
that provides it. On macOS the `cea` extra needs a Fortran compiler; see the
[README](https://github.com/felipebogaertsm/machwave#macos-prerequisite-for-the-cea-extra-gfortran)
for the one-time setup.

## Quick Start

The [Quick Start page](quickstart.md) covers a Solid Rocket Motor simulation.
Propellant selection, grain geometry, nozzle design, simulation execution and result plotting.

For more complete examples, including coupled trajectory with RocketPy and Monte
Carlo simulation, check out the
[examples directory](https://github.com/felipebogaertsm/machwave/tree/main/examples).

## License

Machwave is licensed under the [GNU General Public License v3.0](https://github.com/felipebogaertsm/machwave/blob/main/license.txt).
