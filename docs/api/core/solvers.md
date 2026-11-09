# core.solvers

Numerical ODE solvers used by the simulation engine.

`rk4th_ode_solver` advances a single variable over `d_t` in equal fourth-order Runge-Kutta substeps.
It takes as many substeps as keep each one within one decay time.
It returns the new value and the substep count.
The solid motor chamber pressure is integrated this way, as described in [Integrating the Chamber Pressure](../../explanations/mass_balance.md#integrating-the-chamber-pressure).

`rk4th_step` takes one classical fourth-order Runge-Kutta step for a system of variables.
Only the entries in the state-variable dictionary are advanced through the four stages.
Other keyword arguments are held constant for the whole step.
A source term that depends on an integrated variable must therefore come through the equation callable.

`rk4th_vector_ode_solver` advances an autonomous system $y' = f(y)$, held in one array, over `d_t` in `step_count` equal Runge-Kutta steps.
The biliquid engine integrates its whole state with it.

::: machwave.core.solvers
