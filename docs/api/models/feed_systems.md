# models.feed_systems

Feed-system models for liquid-fed rocket engines. The package describes how
propellant is delivered from the tanks to the combustion chamber, and is
organised around three concerns:

| Concern | Where it lives | What it contains |
| --- | --- | --- |
| Contract | `feed_systems.base` | The abstract [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] interface every cycle must satisfy. |
| Cycle implementations | [`feed_systems.cycles`](feed_systems/cycles.md) | One module per cycle topology (pressure-fed today; electric-pump, gas-generator, expander, staged-combustion to follow). |
| Shared component descriptions | [`feed_systems.components`](feed_systems/components.md) | Static descriptions of pumps, turbines, gas generators, regenerative jackets, plus a tabulated-curve helper that cycle implementations consume. |
| Tank thermodynamics | [`feed_systems.tank`](feed_systems/tank.md) | Two-phase tank model backed by CoolProp (`liquid` extra). |
| Propellant lines | `feed_systems.lines` | The [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] a feed system delivers — its name, its role, the tank it draws from, and optionally the [`TankPlacement`][machwave.models.feed_systems.lines.TankPlacement] of that tank — and the [`LineState`][machwave.models.feed_systems.lines.LineState] the integrator carries for it. |

## The `FeedSystem` contract

A feed system delivers one [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] per propellant, keyed by line name, and every cycle implementation extends [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] to supply the pressure that reaches the injector on every line:

- `get_inlet_pressures(line_states) -> dict[str, float]`

From those, the base class assembles the state every line is fed with:

- `get_inlet_states(line_states) -> dict[str, FluidState]`

Both take the [`LineState`][machwave.models.feed_systems.lines.LineState] of every line — the fluid mass and the internal energy the integrator carries beside it — keyed by line name.

The default inlet state is the tank fluid at the tank temperature and density, at the pressure that survives the path to the injector. A cycle that heats or pressurizes a propellant on the way — a regenerative jacket, a pump — overrides `get_inlet_states` to say so.

[`machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep] composes the two: it reads every inlet state once per integration step, then calls [`Injector`][machwave.models.thrust_chamber.injector.Injector] with them at each chamber pressure the solver tries.

## Tank placement and propellant mass properties

A [`TankPlacement`][machwave.models.feed_systems.lines.TankPlacement] gives a tank its inner diameter and the distance from the nozzle exit to its aft end.
It is optional and does not affect the internal ballistics.

With every tank placed, [`FeedSystem.get_propellant_mass_properties`][machwave.models.feed_systems.base.FeedSystem.get_propellant_mass_properties] returns the propellant center of gravity and inertia in the engine frame.
The biliquid simulation records them every timestep as `propellant_cog` and `propellant_moi`.
The center of gravity is NaN and the inertia zero once every tank is empty or when any line has no placement.

## Public surface

Importing from `machwave.models.feed_systems` exposes the abstract base, every concrete cycle, and the `components` sub-package:

```python
from machwave.models.feed_systems import (
    FeedSystem,
    StackedTankPressureFedFeedSystem,
    components,
)

pump_spec = components.PumpSpec(
    name="oxidizer pump",
    isentropic_efficiency=0.7,
    pressure_rise=5.0e6,
    volumetric_flow_design=2.0e-3,
    shaft_speed_design=3000.0,
)
```

The top-level `machwave` package additionally re-exports `feed_systems` as a shortcut, so `from machwave import feed_systems` and `feed_systems.StackedTankPressureFedFeedSystem` work identically.

::: machwave.models.feed_systems
