# Machwave
## Author: Felipe Bogaerts de Mattos

Machwave is an all-in-one Python package built for simulating rocket engines and motors.

# 1. Introduction

## 1.1. Modules

| Topic | Path | Purpose |
| -------------------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Core math & physics**    | `machwave.core`        | Pure, side-effect-free formulas & algorithms (`flow`, `math`, `structural`, `conversions`, `des`). |
| **Domain models**          | `machwave.models`      | Data-rich objects that describe reality—materials, propellants, motors, grain geometry, rockets, atmosphere, recovery. |
| **State snapshots**        | `machwave.operations`  | Immutable records of simulation state (internal-ballistics steps, flight 1-DoF states, etc.). |
| **Simulation engines**     | `machwave.simulations` | Time-loop drivers that orchestrate models & produce operation streams; includes factory helpers. |
| **Monte-Carlo strategies** | `machwave.montecarlo`  | Runs Monte Carlos simulations. |
| **File I/O**               | `machwave.io`          | Gateways for external formats (e.g., `eng.py` to export RASP *.eng* thrust files). |
| **User-facing services**   | `machwave.services`    | Presentation & convenience: plotting helpers under `services.plots`. |
| **Utility helpers**        | `machwave.common`      | Small, generic helpers (array ops, decorators, misc generics) used by any layer. |

An **import permission matrix** describes which modules can import from one another inside the application. Rules of thumb:

- Arrows always point outward; a layer may only import the ones marked ✓ in its row.
- No layer ever imports inward (up the column).
- services is the outer facade - everything can be used there; common is the innermost helper layer - nothing else is imported by it.

| *From / To*     | common | core | models | operations | simulations | montecarlo |  io | services |
| --------------- | :----: | :--: | :----: | :--------: | :---------: | :--------: | :-: | :------: |
| **common**      |    ✗   |   ✗  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **core**        |    ✓   |   ✗  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **models**      |    ✓   |   ✓  |    ✗   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **operations**  |    ✓   |   ✓  |    ✓   |      ✗     |      ✗      |      ✗     |  ✗  |     ✗    |
| **simulations** |    ✓   |   ✓  |    ✓   |      ✓     |      ✗      |      ✗     |  ✓  |     ✗    |
| **montecarlo**  |    ✓   |   ✓  |    ✓   |      ✓     |      ✓      |      ✗     |  ✓  |     ✗    |
| **io**          |    ✓   |   ✓  | (rare) |   (rare)   |      ✗      |      ✗     |  ✗  |     ✗    |
| **services**    |    ✓   |   ✓  |    ✓   |      ✓     |      ✓      |      ✓     |  ✓  |     ✗    |

# 2. Models

Models are object representations of physical devices or phenomena. They represent things such as a rocket's fuselage, a motor/engine nozzle, a combustion chamber, and more.

# 3. Simulations

Machwave currently supports internal ballistics simulations for solid motors and liquid engines and point-mass trajectory simulations.

Simulation classes receive the models to be simulated (rockets, motors, and/or engines) and a SimulationParams class instance, specific for each simulation type.

Internally, one or more Operations class is instantiated to handle the simulation states. Inside Operations is where the time-history arrays are stored, such as thrust, altitude, chamber pressure, and others.