# models.feed_systems

Feed-system models for liquid-fed rocket engines. The package describes how
propellant is delivered from the tanks to the combustion chamber, and is
organised around three concerns:

| Concern | Where it lives | What it contains |
| --- | --- | --- |
| Contract | `feed_systems.base` | The abstract [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] interface every cycle must satisfy. |
| Cycle implementations | [`feed_systems.cycles`](feed_systems/cycles.md) | One module per cycle topology (pressure-fed today; electric-pump, gas-generator, expander, staged-combustion to follow). |
| Shared component descriptions | [`feed_systems.components`](feed_systems/components.md) | Static descriptions of pumps, turbines, gas generators, regenerative jackets, plus a tabulated-curve helper that cycle implementations consume. |
| Tank thermodynamics | [`feed_systems.tank`](feed_systems/tank.md) | Two-phase tank model backed by CoolProp. |
| Propellant lines | `feed_systems.lines` | The [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] a feed system delivers — its name, its role, and the tank it draws from — and the [`LineState`][machwave.models.feed_systems.lines.LineState] the integrator carries for it. |

## The `FeedSystem` contract

A feed system delivers one [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] per propellant, keyed by line name, and every cycle implementation extends [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] to supply the pressure that reaches the injector on every line:

- `get_inlet_pressures(line_states) -> dict[str, float]`

From those, the base class assembles the state every line is fed with:

- `get_inlet_states(line_states) -> dict[str, FluidState]`

Both take the [`LineState`][machwave.models.feed_systems.lines.LineState] of every line — the fluid mass and the internal energy the integrator carries beside it — keyed by line name. Solving all the lines in one call is what the physics asks for: a cycle couples its lines, as the stacked-tank piston ties the fuel pressure to the oxidizer ullage pressure.

Keying by name is what makes the propellant count free. A biliquid engine feeds an oxidizer line and a fuel line; a triliquid adds a third with the `ADDITIVE` role for a diluent or a coolant; an oxidizer-only hybrid feed and a monoliquid are the one-line case of the same contract.

The default inlet state is the tank fluid at the tank temperature and density, at the pressure that survives the path to the injector. A cycle that heats or pressurizes a propellant on the way — a regenerative jacket, a pump — overrides `get_inlet_states` to say so.

The feed system is responsible for everything upstream of the injector face (tank state, piston and feedline losses, pump discharge, jacket pickup); the injector owns the orifice physics (discharge coefficient, area, and the per-line `MassFlowModel` that selects between single-phase incompressible and homogeneous-equilibrium two-phase flow). A [`FluidState`][machwave.common.fluid_state.FluidState] is the whole of what passes between them, so neither package imports the other — both depend only on the shared value object.

[`machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep] composes the two: it reads every inlet state once per integration step, then calls [`Injector`][machwave.models.thrust_chamber.injector.Injector] with them at each chamber pressure the solver tries.

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
