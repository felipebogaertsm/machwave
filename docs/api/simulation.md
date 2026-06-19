# Simulation

Main entry point for running internal ballistics simulations. `InternalBallisticsSimulation` takes a motor model and simulation parameters (time step, igniter pressure, external pressure), then marches through time using an RK4 solver.

`run()` returns a frozen `SimulationResult` (subclassed per motor type — `SolidSimulationResult`, `BiliquidSimulationResult`) carrying the full time-series data (thrust, chamber pressure, propellant mass, efficiency losses, …) along with derived scalars (total impulse, specific impulse, burn time). Each result class provides a `report()` method to print a human-readable summary and a `summary()` method that returns the scalar metrics as a dict.

The per-step accumulator state used by the integrator (`MotorState` and its subclasses `SolidMotorState`, `BiliquidEngineState`) lives in this same package — it is rarely consumed directly outside the simulation loop. Alongside it, the abstract `TimestepConditions` and its per-engine subclasses `SolidTimestepConditions`, `BiliquidTimestepConditions` snapshot the operating quantities of one timestep and are handed to the nozzle loss model.

::: machwave.simulation
    options:
      show_submodules: true
