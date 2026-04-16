# core.solvers

Numerical ODE solvers used by the simulation engine.

Provides a classical 4th-order Runge-Kutta integrator (`rk4th_ode_solver`) that advances the internal ballistics state at each time step. Accepts a generic equation callable and a dictionary of state variables, returning updated values after one step of size `d_t`.

::: machwave.core.solvers
