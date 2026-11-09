# core.solvers

Numerical ODE solvers used by the simulation engine.

Provides a classical 4th-order Runge-Kutta integrator (`rk4th_ode_solver`) that advances the internal ballistics state at each time step. Accepts a generic equation callable and a dictionary of state variables, returning updated values after one step of size `d_t`.

Only the entries in the state-variable dictionary are advanced through the four stages; any other keyword arguments are held constant for the whole step. A source term that depends on an integrated variable must be supplied through the equation callable rather than as a precomputed constant.

`rk4th_substepped_ode_solver` advances a single variable over `d_t` in as many equal Runge-Kutta steps as the equation's stiffness requires, so each step satisfies $|\lambda| \Delta t \le 1$, with $\lambda$ the derivative of the right-hand side with respect to the variable.

::: machwave.core.solvers
