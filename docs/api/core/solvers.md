# core.solvers

Numerical ODE solvers used by the simulation engine.

`rk4th_ode_solver` advances the chamber pressure in fourth-order Runge-Kutta substeps, as described in [Integrating the Chamber Pressure](../../explanations/mass_balance.md#integrating-the-chamber-pressure).
`rk4th_step` takes one classical fourth-order Runge-Kutta step for a system of variables.

::: machwave.core.solvers
