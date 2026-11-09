# core.solvers

Numerical ODE solvers used by the simulation engine.

`rk4th_ode_solver` takes one classical fourth-order Runge-Kutta step of size `d_t` for a system of variables. It accepts a generic equation callable and a dictionary of state variables, and returns the updated values.

Only the entries in the state-variable dictionary are advanced through the four stages; any other keyword arguments are held constant for the whole step. A source term that depends on an integrated variable must be supplied through the equation callable rather than as a precomputed constant.

`rk4th_substepped_ode_solver` advances a single variable over `d_t` in $N$ equal Runge-Kutta substeps, with $N$ chosen so that $|\lambda| \Delta t / N \le 1$, where $\lambda$ is the derivative of the right-hand side with respect to the variable. It returns the new value and $N$. The chamber pressure is integrated this way; the reasoning is in [Integrating the Chamber Pressure](../../explanations/mass_balance.md#integrating-the-chamber-pressure).

::: machwave.core.solvers
