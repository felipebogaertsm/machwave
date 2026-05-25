# Core

The engineering math layer. Contains unit conversions, geometric primitives (circle/cylinder areas, contour extraction), compressible and incompressible flow relations, nozzle performance calculations, and mechanical properties (CoG, inertia tensors).

Submodules:

- [compressible_flow](core/compressible_flow.md) — Isentropic relations, thrust coefficients, nozzle loss models
- [mass_balance](core/mass_balance.md) — Chamber-pressure ODE shared by SRM and LRE
- [solvers](core/solvers.md) — RK4 ODE solver

::: machwave.core
