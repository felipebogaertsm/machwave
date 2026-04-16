# core.compressible_flow

Compressible flow relations for convergent-divergent nozzle analysis.

- **Isentropic flow** — Critical pressure ratio, exit Mach from expansion ratio, exit pressure, choked-flow detection.
- **Nozzle performance** — Ideal and corrected thrust coefficient (Cf), optimal expansion ratio for a given altitude, thrust from Cf.
- **Loss models** — Percentage-based correction factors for divergent angle, finite-rate kinetics, boundary layer, and two-phase flow losses. These combine into an overall nozzle efficiency applied to the ideal Cf.

All loss functions return values in the 0–100% range and follow standard empirical correlations from Humble, Henry & Larson.

::: machwave.core.compressible_flow
