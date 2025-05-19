# Machwave

Machwave is a Python library for modelling solid rocket motors, liquid rocket engines, and whole vehicles, then running high-fidelity internal-ballistics and point-mass flight simulations—all with a clean, layered architecture.

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

# Modules

| Topic | Path | Purpose |
| -------------------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Core math & physics**    | `machwave.core`        | Pure, side-effect-free formulas & algorithms (`flow`, `math`, `structural`, `conversions`, `des`). |
| **Domain models**          | `machwave.models`      | Data-rich objects that describe reality—materials, propellants, motors, grain geometry, rockets, atmosphere, recovery. |
| **Simulation states**        | `machwave.states`  | Immutable records of simulation state (internal-ballistics steps, flight 1-DoF states, etc.). |
| **Simulation engines**     | `machwave.simulations` | Time-loop drivers that orchestrate models & produce state streams; includes factory helpers. |
| **Monte-Carlo strategies** | `machwave.montecarlo`  | Runs Monte Carlos simulations. |
| **File I/O**               | `machwave.io`          | Gateways for external formats (e.g., `eng.py` to export RASP *.eng* thrust files). |
| **User-facing services**   | `machwave.services`    | Presentation & convenience: plotting helpers under `services.plots`. |
| **Utility helpers**        | `machwave.common`      | Small, generic helpers (array ops, decorators, misc generics) used by any layer. |

An **import permission matrix** describes which modules can import from one another inside the application. Rules of thumb:

- Arrows always point outward; a layer may only import the ones marked ✓ in its row.
- No layer ever imports inward (up the column).
- services is the outer facade - everything can be used there; common is the innermost helper layer - nothing else is imported by it.

| *From / To*     | common | core | models | states | simulations | montecarlo |  io | services |
| --------------- | :----: | :--: | :----: | :--------: | :---------: | :--------: | :-: | :------: |
| **common**      |    ✗   |   ✗  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **core**        |    ✓   |   ✗  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **models**      |    ✓   |   ✓  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **states**  |    ✓   |   ✓  |    ✓   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **simulations** |    ✓   |   ✓  |    ✓   |      ✓     |      ✗      |      ✗     |  ✓  |     ✗    |
| **montecarlo**  |    ✓   |   ✓  |    ✓   |      ✓     |      ✓      |      ✗     |  ✓  |     ✗    |
| **io**          |    ✓   |   ✓  | (rare) |   (rare)   |      ✗      |      ✗     |  ✗  |     ✗    |
| **services**    |    ✓   |   ✓  |    ✓   |      ✓     |      ✓      |      ✓     |  ✓  |     ✗    |

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