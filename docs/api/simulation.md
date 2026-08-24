# Simulation

Main entry point for running internal ballistics simulations. `InternalBallisticsSimulation` takes a motor model and simulation parameters (time step, igniter pressure, external pressure), then marches through time using an RK4 solver.

The run ends on whichever of these two conditions fires first:

| Condition | Fires when | Ends |
| --- | --- | --- |
| Loss of choking | Chamber pressure falls to the critical ratio of the ambient pressure, roughly 1.7 to 1.8 times `external_pressure` | Runs against an atmosphere |
| Tail-off | The motor has burnt out **and** thrust has decayed to `TAIL_OFF_THRUST_FRACTION` (0.1%) of its peak | Vacuum and upper stage runs, where the nozzle stays choked all the way down |

`run()` returns a frozen `SimulationResult` (subclassed per motor type — `SolidSimulationResult`, `BiliquidSimulationResult`) carrying the full time-series data (thrust, chamber pressure, propellant mass, efficiency losses, …) along with derived scalars (total impulse, specific impulse, burn time). Each result class provides a `report()` method to print a human-readable summary and a `summary()` method that returns the scalar metrics as a dict.

The per-step accumulator state used by the integrator (`MotorState` and its subclasses `SolidMotorState`, `BiliquidEngineState`) lives in this same package — it is rarely consumed directly outside the simulation loop. Alongside it, the abstract `TimestepConditions` and its per-engine subclasses `SolidTimestepConditions`, `BiliquidTimestepConditions` snapshot the operating quantities of one timestep and are handed to the nozzle loss model.

::: machwave.simulation
    options:
      show_submodules: true
