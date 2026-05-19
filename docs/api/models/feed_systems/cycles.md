# models.feed_systems.cycles

Concrete feed-system cycle implementations. A *cycle* is the topology that determines how propellant is pressurised on its way from the tanks to the injector — pressure stored in the tanks themselves, electrically driven pumps, turbine-driven pumps powered by a small bleed-off combustor, and so on. Each module in this sub-package implements one topology and conforms to the [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] contract so the simulation loop can treat them interchangeably.

## Available cycles

- [`StackedTankPressureFedFeedSystem`](#stackedtankpressurefedfeedsystem) — Pressure-fed engine with the oxidizer tank stacked directly above a piston-separated fuel tank. Tank pressure provides both propellants' driving head.

Additional cycles are under active development as separate work items: electric-pump, gas-generator, expander, and staged-combustion. When they land, they will reuse the dataclasses in [`feed_systems.components`](components.md) to describe their pumps, turbines, gas generators, and regenerative jackets.

## How cycles compose with the rest of the engine

```
┌──────────────┐  ┌──────────────────────┐  ┌──────────┐  ┌──────────┐
│ tanks.Tank   │──│ feed_systems.cycles  │──│ injector │──│ chamber  │
│ (two-phase)  │  │  (this sub-package)  │  │          │  │          │
└──────────────┘  └──────────────────────┘  └──────────┘  └──────────┘
                       ▲           ▲
                       │           │
                  feed_systems.components
                  (pump/turbine/gas-generator
                   /regenerative-jacket specs)
```

The cycle reads tank state via the [`Tank`][machwave.models.feed_systems.tanks.base.Tank] instances it was constructed with, and combines that state with any [component specs](components.md) it owns to evaluate mass flow through the injector. The simulation step lives in [`LiquidEngineState.run_timestep`][machwave.simulation.liquid.states.LiquidEngineState.run_timestep], which calls `get_mass_flow_ox` and `get_mass_flow_fuel` once per integration step with the current `chamber_pressure` and the injector geometry from the [`BipropellantInjector`][machwave.models.thrust_chamber.injector.BipropellantInjector].

---

## `StackedTankPressureFedFeedSystem`

A bipropellant pressure-fed engine in which the oxidizer and fuel tanks are arranged as a single vertical stack separated by a piston. The oxidizer tank pressure pressurises both propellants — directly for the oxidizer, and indirectly for the fuel through the piston. Pressure loss across the piston is captured by `piston_loss`.

**Construction**

```python
from machwave.models.feed_systems import StackedTankPressureFedFeedSystem
from machwave.models.feed_systems.tanks import Tank

feed_system = StackedTankPressureFedFeedSystem(
    oxidizer_line_diameter=0.010,    # m
    oxidizer_line_length=0.5,        # m
    fuel_line_diameter=0.008,        # m
    fuel_line_length=0.5,            # m
    fuel_tank=Tank("Ethanol", volume=0.008, temperature=298.0, initial_fluid_mass=3.0),
    oxidizer_tank=Tank("N2O",   volume=0.010, temperature=298.0, initial_fluid_mass=5.0),
    piston_loss=0.0,                  # Pa
)
```

**Mass-flow model.** Each propellant's mass flow is evaluated with the injector orifice equation via `get_mass_flow_orifice` (in [`machwave.core.incompressible_flow`](../../core.md)):

\[
\dot{m} = C_d \cdot A \cdot \sqrt{2 \rho \left(P_\text{up} - P_\text{down}\right)}
\]

with $P_\text{up}$ equal to the oxidizer tank pressure for the oxidizer branch and to `oxidizer_tank_pressure - piston_loss` for the fuel branch, $P_\text{down}$ equal to `chamber_pressure`, and $\rho$ the saturated-liquid density returned by [`Tank.get_density`][machwave.models.feed_systems.tanks.base.Tank.get_density].

Line geometry (`oxidizer_line_diameter`, `oxidizer_line_length`, `fuel_line_diameter`, `fuel_line_length`) is currently stored on the instance for downstream issues that will add feedline pressure drop, but is not consumed by the mass-flow model itself yet.

---

::: machwave.models.feed_systems.cycles
