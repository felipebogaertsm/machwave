# core.compressible_flow

Compressible flow relations for convergent-divergent nozzle analysis.

- **Isentropic flow** — Critical pressure ratio, exit Mach from expansion ratio, exit pressure, choked-flow detection.
- **Nozzle performance** — Ideal and corrected thrust coefficient (Cf), optimal expansion ratio for a given altitude, effective exit conditions under overexpanded flow separation, thrust from Cf.
- **Loss models** — Fractional correction factors for divergent angle, finite-rate kinetics, boundary layer, and two-phase flow losses. These combine into an overall nozzle efficiency applied to the ideal Cf.

All loss functions return a loss as a fraction in [0, 1] and follow the empirical correlations of Coats et al. (AFRPL-TR-75-36, 1975).

::: machwave.core.compressible_flow
