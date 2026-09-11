<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo/machwave-lockup-white.svg">
    <img src="docs/assets/logo/machwave-lockup-color.svg" alt="Machwave" width="400">
  </picture>
</p>

Machwave is a Python library for chemical propulsion simulation. The library makes it
easy to model solid or biliquid rocket engines, analyse performance and integrate the
results into trajectory simulations.

## Getting Started

### Installation

Install Machwave using pip:

```bash
pip install machwave
```

The core install depends only on NumPy, SciPy and fluids. It runs a complete solid
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
that provides it.

#### macOS prerequisite for the `cea` extra: gfortran

Only needed if you install the `cea` extra, directly or through `all`.
[rocketcea](https://pypi.org/project/RocketCEA/) does not publish macOS wheels on
PyPI. On macOS, pip therefore builds rocketcea from source and needs a Fortran
compiler. Homebrew's `gcc` formula installs only versioned binaries (e.g.
`gfortran-15`), so an unversioned `gfortran` symlink must be added to `PATH`
beforehand:

```bash
brew install gcc
ln -sf "$(ls "$(brew --prefix)"/bin/gfortran-* | sort -V | tail -n 1)" "$(brew --prefix)/bin/gfortran"
```

Linux and Windows users do not need this step — rocketcea ships prebuilt wheels
for those platforms.

### Documentation

The full documentation is available at
[felipebogaertsm.github.io/machwave](http://felipebogaertsm.github.io/machwave/).

### Development Setup

If you're contributing to Machwave, you'll need [uv](https://docs.astral.sh/uv/) for dependency management.

#### Installing uv

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For more details, visit the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

#### Clone and Install

Clone the repository and install dependencies:

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
make install-dev
```

`make install-dev` installs every extra alongside the development tooling, which is
what the test suite and the type checker need. `make install-dev-core` installs the
tooling without the extras, the environment `make test-core` runs against.

#### Publishing a New Release

1. **Create a release** on GitHub with a tag matching `vX.Y.Z` (e.g. `v1.2.0`).
   The version is derived automatically from the git tag.

2. The publish workflow builds the package and publishes it to PyPI via trusted publishing (OIDC).
