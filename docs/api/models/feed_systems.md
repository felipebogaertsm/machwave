# models.feed_systems

Feed-system models for biliquid rocket engines. The package describes how
propellant is delivered from the tanks to the combustion chamber, and is
organised around three concerns:

| Concern | Where it lives | What it contains |
| --- | --- | --- |
| Contract | `feed_systems.base` | The abstract [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] interface every cycle must satisfy. |
| Cycle implementations | [`feed_systems.cycles`](feed_systems/cycles.md) | One module per cycle topology (pressure-fed today; electric-pump, gas-generator, expander, staged-combustion to follow). |
| Shared component descriptions | [`feed_systems.components`](feed_systems/components.md) | Static descriptions of pumps, turbines, gas generators, regenerative jackets, plus a tabulated-curve helper that cycle implementations consume. |
| Tank thermodynamics | [`feed_systems.tanks`](feed_systems/tanks.md) | Two-phase tank model backed by CoolProp. |

## The `FeedSystem` contract

Every cycle implementation extends [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] and exposes four methods used by the simulation loop:

- `get_mass_flow_ox(chamber_pressure, *, discharge_coefficient=None, injector_area=None) -> float`
- `get_mass_flow_fuel(chamber_pressure, *, discharge_coefficient=None, injector_area=None) -> float`
- `get_oxidizer_tank_pressure() -> float`
- `get_fuel_tank_pressure() -> float`

`discharge_coefficient` and `injector_area` are keyword-only with `None` defaults: pressure-fed cycles need them to evaluate the injector orifice equation, while turbopump cycles that schedule mass flow from pump-curve solutions do not. Keeping the keywords on the abstract base means a single call site in the integrator works against either kind of cycle.

The concrete propellant mass-flow consumer is [`machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep], which always passes the keywords explicitly — code calling these methods should follow the same pattern.

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
