# Core

The engineering math layer. Contains unit conversions, geometric primitives (circle/cylinder areas, contour extraction), compressible and incompressible flow relations, nozzle performance calculations, and mechanical properties (CoG, inertia tensors).

Submodules:

- [compressible_flow](core/compressible_flow.md) — Isentropic relations, thrust coefficients, nozzle loss models
- [interpolation](core/interpolation.md) — Non-extrapolating bounded cubic spline for tabulated curves
- [mass_balance](core/mass_balance.md) — Chamber-pressure ODE shared by solid motors and biliquid engines
- [performance](core/performance.md) — Total and specific impulse
- [solvers](core/solvers.md) — RK4 ODE solver

::: machwave.core
