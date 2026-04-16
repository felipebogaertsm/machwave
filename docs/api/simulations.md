# Simulation

Main entry point for running internal ballistics simulations. `InternalBallisticsSimulation` takes a motor model and simulation parameters (time step, igniter pressure, external pressure), then marches through time using an RK4 solver to produce a complete motor state with time-series data for thrust, chamber pressure, propellant mass, efficiency losses, and more.

The returned `MotorState` object (see [states](states.md)) contains all computed arrays for post-processing or adapter export.

::: machwave.simulation
