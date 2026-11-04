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
| Propellant lines | `feed_systems.lines` | The [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] a feed system delivers (its name, its role, the tank it draws from and the [`FeedlineResistance`][machwave.models.feed_systems.lines.FeedlineResistance] of its plumbing) and the [`LineState`][machwave.models.feed_systems.lines.LineState] the integrator carries for it. |

## The `FeedSystem` contract

A feed system delivers one [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] per propellant, keyed by line name, and every cycle implementation extends [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] to supply the pressure at the head of every feedline:

- `get_inlet_pressures(line_states) -> dict[str, float]`

From those, the base class assembles the state every line is fed with:

- `get_inlet_states(line_states) -> dict[str, FluidState]`

Both take the [`LineState`][machwave.models.feed_systems.lines.LineState] of every line — the fluid mass and the internal energy the integrator carries beside it — keyed by line name.

The default state is the tank fluid at the tank temperature and density, at the pressure the cycle delivers to the feedline. The feedline loss is not in it: it depends on the line flow, which the injector sets, so the simulation solves the two together per line. A cycle that heats or pressurizes a propellant on the way, such as a regenerative jacket or a pump, overrides `get_inlet_states` to say so.

[`machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep] composes the two: it reads every feedline head state once per integration step, then, at each chamber pressure the solver tries, solves every line's flow through its [`Injector`][machwave.models.thrust_chamber.injector.Injector] element with the line's own flow-dependent loss.

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
