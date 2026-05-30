<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo/machwave-lockup-white.png">
    <img src="docs/assets/logo/machwave-lockup-color.png" alt="Machwave" width="400">
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

#### macOS prerequisite: gfortran

Machwave depends on [rocketcea](https://pypi.org/project/RocketCEA/), which does
not publish macOS wheels on PyPI. On macOS, pip therefore builds rocketcea from
source and needs a Fortran compiler. Homebrew's `gcc` formula installs only
versioned binaries (e.g. `gfortran-15`), so an unversioned `gfortran` symlink
must be added to `PATH` before `pip install machwave`:

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
make install
```

#### Publishing a New Release

1. **Create a release** on GitHub with a tag matching `vX.Y.Z` (e.g. `v1.2.0`).
   The version is derived automatically from the git tag.

2. The publish workflow builds the package and publishes it to PyPI via trusted publishing (OIDC).
