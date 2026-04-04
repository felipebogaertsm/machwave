# Machwave

Machwave is a Python library for chemical propulsion simulation. The library makes it
easy to model solid or liquid rocket engines, analyse performance and integrate the
results into trajectory simulations.

## Getting Started

### Installation

Install Machwave using pip:

```bash
pip install machwave
```

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
