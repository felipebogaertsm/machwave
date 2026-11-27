# core.solvers

Numerical ODE solvers used by the simulation engine.

`rk4.integrate_scalar_ode` integrates the chamber pressure over a simulation time step in as many fourth-order Runge-Kutta steps as stability needs, as described in [Integrating the Chamber Pressure](../../explanations/mass_balance.md#integrating-the-chamber-pressure).
`rk4.step_ode_system` takes one classical fourth-order Runge-Kutta step for a system of variables.

::: machwave.core.solvers.rk4
