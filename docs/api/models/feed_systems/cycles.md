# models.feed_systems.cycles

Concrete feed-system cycle implementations. A *cycle* is the topology that determines how propellant is pressurised on its way from the tanks to the injector — pressure stored in the tanks themselves, electrically driven pumps, turbine-driven pumps powered by a small bleed-off combustor, and so on. Each module in this sub-package implements one topology and conforms to the [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] contract so the simulation loop can treat them interchangeably.

## Available cycles

- [`StackedTankPressureFedFeedSystem`](#stackedtankpressurefedfeedsystem) — Pressure-fed engine with the oxidizer tank stacked directly above a piston-separated fuel tank. Tank pressure provides both propellants' driving head.
- [`SingleLinePressureFedFeedSystem`](#singlelinepressurefedfeedsystem) — Pressure-fed engine feeding one line, which the tank pressurizes itself. The one-line case of the contract: an oxidizer-only hybrid feed or a monoliquid.

The cycle reads tank state through the [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] instances it was constructed with, and combines that state with any [component specs](components.md) it owns to say what reaches the injector face. The simulation step lives in [`BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep], which calls `get_inlet_states` once per integration step and hands the results to the [`Injector`][machwave.models.thrust_chamber.injector.Injector] at each chamber pressure the solver tries.

---

## `StackedTankPressureFedFeedSystem`

A pressure-fed engine whose propellant tanks are arranged as a single vertical stack separated by a piston. The tank at the top of the stack — `pressurizing_line` — pressurises every propellant: directly for its own line, and through the piston for every line below it. Pressure loss across the piston is captured by `piston_loss`, and each feedline takes what `line_losses` states for it.

**Construction**

The two-line case a biliquid engine runs on has a convenience constructor, which names the lines `"oxidizer"` and `"fuel"`:

```python
from machwave.models.feed_systems import StackedTankPressureFedFeedSystem
from machwave.models.feed_systems.tank import Tank

feed_system = StackedTankPressureFedFeedSystem.from_oxidizer_and_fuel(
    oxidizer_tank=Tank("N2O", volume=0.010, temperature=298.0, initial_fluid_mass=5.0),
    fuel_tank=Tank("Ethanol", volume=0.008, temperature=298.0, initial_fluid_mass=3.0),
    piston_loss=0.0,          # Pa
    oxidizer_line_loss=2e5,   # Pa
    fuel_line_loss=2e5,       # Pa
)
```

Any other propellant count is built from the lines themselves — here a triliquid with a diluent below the piston:

```python
from machwave.models.feed_systems import PropellantLine, StackedTankPressureFedFeedSystem
from machwave.models.propellants import ComponentRole

feed_system = StackedTankPressureFedFeedSystem(
    lines=[
        PropellantLine(name="oxidizer", role=ComponentRole.OXIDIZER, tank=oxidizer_tank),
        PropellantLine(name="fuel", role=ComponentRole.FUEL, tank=fuel_tank),
        PropellantLine(name="diluent", role=ComponentRole.ADDITIVE, tank=diluent_tank),
    ],
    pressurizing_line="oxidizer",
    piston_loss=1e5,
    line_losses={"oxidizer": 2e5, "fuel": 2e5, "diluent": 1e5},
)
```

**Mass-flow model.** The feed system supplies the inlet state of every line and the injector does the orifice dispatch. Inlet pressure is the pressurizing tank pressure for its own line and that pressure less `piston_loss` for every line below the piston, each less its own feedline loss; downstream pressure is `chamber_pressure`. Inlet density comes from [`Tank.get_density`][machwave.models.feed_systems.tank.Tank.get_density]. The injector picks the orifice model per line from its [`MassFlowModel`][machwave.models.thrust_chamber.injector.MassFlowModel].

`line_losses` is a fixed pressure drop per line, not a function of flow.

---

## `SingleLinePressureFedFeedSystem`

One propellant line, pressurized by its own tank: a self-pressurized propellant rides its vapor pressure while liquid remains, then blows down on the real-gas equation of state. What reaches the injector is that pressure less `line_loss`. An empty tank delivers nothing, which stops the flow at the injector element.

**Construction**

```python
from machwave.models.feed_systems import SingleLinePressureFedFeedSystem
from machwave.models.feed_systems.tank import Tank

feed_system = SingleLinePressureFedFeedSystem.from_oxidizer_tank(
    oxidizer_tank=Tank("N2O", volume=0.010, temperature=298.0, initial_fluid_mass=5.0),
    line_loss=2e5,  # Pa
)
```

A monoliquid names its own line and role instead, through the `PropellantLine` constructor.

---

::: machwave.models.feed_systems.cycles
