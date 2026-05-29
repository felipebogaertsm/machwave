# models.feed_systems

Feed-system models for biliquid rocket engines. The package describes how
propellant is delivered from the tanks to the combustion chamber, and is
organised around three concerns:

| Concern | Where it lives | What it contains |
| --- | --- | --- |
| Contract | `feed_systems.base` | The abstract [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] interface every cycle must satisfy. |
| Cycle implementations | [`feed_systems.cycles`](feed_systems/cycles.md) | One module per cycle topology (pressure-fed today; electric-pump, gas-generator, expander, staged-combustion to follow). |
| Shared component descriptions | [`feed_systems.components`](feed_systems/components.md) | Static descriptions of pumps, turbines, gas generators, regenerative jackets, plus a tabulated-curve helper that cycle implementations consume. |
| Tank thermodynamics | [`feed_systems.tank`](feed_systems/tank.md) | Two-phase tank model backed by CoolProp. |

## The `FeedSystem` contract

Every cycle implementation extends [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] and exposes four methods used by the simulation loop:

- `get_mass_flow_ox(chamber_pressure, *, injector) -> float`
- `get_mass_flow_fuel(chamber_pressure, *, injector) -> float`
- `get_oxidizer_tank_pressure() -> float`
- `get_fuel_tank_pressure() -> float`

The mass-flow methods take a [`BipropellantInjector`][machwave.models.thrust_chamber.injector.BipropellantInjector] and delegate the orifice dispatch to it. The feed system is responsible for computing the upstream pressure (tank state, piston losses, pump discharge); the injector owns the orifice physics (discharge coefficient, area, and the per-side `MassFlowModel` that selects between single-phase incompressible and homogeneous-equilibrium two-phase flow). This split lets pump-fed cycles substitute a different upstream-pressure source without touching orifice physics.

The concrete propellant mass-flow consumer is [`machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep], which calls these methods once per integration step with the current `chamber_pressure` and the [`BipropellantInjector`][machwave.models.thrust_chamber.injector.BipropellantInjector] from the thrust chamber.

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
