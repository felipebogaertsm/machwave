# Simulation

Main entry point for running internal ballistics simulations. `InternalBallisticsSimulation` takes a motor model and simulation parameters (time step, igniter pressure, external pressure), then marches through time using an RK4 solver.

The run ends on whichever of these two conditions fires first:

| Condition | Fires when | Ends |
| --- | --- | --- |
| Loss of choking | Chamber pressure falls to the critical ratio of the ambient pressure, roughly 1.7 to 1.8 times `external_pressure` | Runs against an atmosphere |
| Tail-off | The motor has burnt out **and** thrust has decayed to `TAIL_OFF_THRUST_FRACTION` (0.1%) of its peak | Vacuum and upper stage runs, where the nozzle stays choked all the way down |

- With `external_pressure=0.0` the nozzle stays choked at any chamber pressure, so loss of choking never fires and tail-off is what ends the run.
- Tail-off only fires first for a motor peaking around 175 MPa or more, so it leaves runs against an atmosphere untouched.
- Stopping at tail-off costs almost no impulse: under 0.002% of the total for the motors under test. The 0.1% threshold matches [openMotor](https://github.com/reilleya/openMotor)'s default, alongside the NFPA 1125 (5%) and JANNAF (10%) conventions for burn and action time.

Which condition fired, and when, is on the result: `end_thrust` and `end_burn` flag whether thrust terminated and whether the motor burnt out, while `thrust_time` and `burn_time` date each event [s].

`run()` returns a frozen `SimulationResult` (subclassed per motor type — `SolidSimulationResult`, `BiliquidSimulationResult`) carrying the full time-series data (thrust, chamber pressure, propellant mass, efficiency losses, …) along with derived scalars (total impulse, specific impulse, burn time). Each result class provides a `report()` method to print a human-readable summary and a `summary()` method that returns the scalar metrics as a dict.

The per-step accumulator state used by the integrator (`MotorState` and its subclasses `SolidMotorState`, `BiliquidEngineState`) lives in this same package — it is rarely consumed directly outside the simulation loop. Alongside it, the abstract `TimestepConditions` and its per-engine subclasses `SolidTimestepConditions`, `BiliquidTimestepConditions` snapshot the operating quantities of one timestep and are handed to the nozzle loss model.

::: machwave.simulation
    options:
      show_submodules: true
