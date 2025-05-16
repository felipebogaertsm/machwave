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
