# core.solvers

Numerical ODE solvers used by the simulation engine.

Provides a classical 4th-order Runge-Kutta integrator (`rk4th_ode_solver`) that advances the internal ballistics state at each time step. Accepts a generic equation callable and a dictionary of state variables, returning updated values after one step of size `d_t`.

Only the entries in the state-variable dictionary are advanced through the four stages; any other keyword arguments are held constant for the whole step. A source term that depends on an integrated variable (such as the pressure-dependent chamber inflow) must therefore be supplied through the equation callable — for example, as a callable evaluated at each stage pressure — rather than as a precomputed constant.

::: machwave.core.solvers
