# core.solvers

Numerical ODE solvers used by the simulation engine.

`rk4th_ode_solver` advances the solid motor chamber pressure in fourth-order Runge-Kutta substeps, as described in [Integrating the Chamber Pressure](../../explanations/mass_balance.md#integrating-the-chamber-pressure).
`rk4th_step` takes one classical fourth-order Runge-Kutta step for a system of variables.

`rk4th_vector_ode_solver` advances an autonomous system $y' = f(y)$, held in one array, over `time_step` in `step_count` equal Runge-Kutta steps.
The biliquid engine integrates its whole state with it.

::: machwave.core.solvers
