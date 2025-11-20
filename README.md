# Machwave

Machwave is a Python library for modelling solid rocket motors, liquid rocket engines, and whole vehicles, then running high-fidelity internal-ballistics and point-mass flight simulations—all with a clean, layered architecture.

## Getting Started

### Installation

Install Machwave using pip:

```bash
pip install machwave
```

### Development Setup

If you're contributing to Machwave, you'll need [Poetry](https://python-poetry.org/) for dependency management.

#### Installing Poetry

**macOS / Linux / Ubuntu:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

After installation, verify it worked:

```bash
poetry --version
```

For more details, visit the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

#### Clone and Install

Clone the repository and install dependencies:

```bash
git clone https://github.com/felipebogaertsm/machwave.git
cd machwave
make install
```

# Main features

- Transient Solid Rocket Motor simulation
  - Transient mass-balance chamber pressure calculations
  - Wide variety of grain geometries and configurations
  - Calculated correction factors
- Transient Liquid Rocket Engine simulation (beta)
  - Transient mass-balance chamber pressure calculations
  - Supports multiple types of pressure feed systems
  - High-fidelity propellant models with RocketCEA
- Point-mass trajectory simulation
- Monte Carlo simulations
  - All previous simulations can be executed through the Monte Carlo method
  - Any parameter can be randomized
  - Simulation analysis tooling built-in

# Main components

## Models

Models contain data-rich Python classes that mirror physical hardware or environments. Each model encapsulates state and invariants only (no time marching, no plotting).

## Simulations

Machwave currently supports internal ballistics simulations for solid motors and liquid engines and point-mass trajectory simulations.

A simulation class is the engine that drives the time loop.
It receives:

- the models to be simulated (rocket, motor/engine, etc.);
- a SimulationParams instance tailored to that simulation type.

During execution the solver instantiates one or more SimulationState objects that hold the evolving state arrays - chamber pressure, thrust, altitude, and so on, providing a clean, immutable record of the run.
