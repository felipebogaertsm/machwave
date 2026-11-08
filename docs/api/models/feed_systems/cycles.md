# models.feed_systems.cycles

Concrete feed-system cycle implementations. A *cycle* is the topology that determines how propellant is pressurised on its way from the tanks to the injector — pressure stored in the tanks themselves, electrically driven pumps, turbine-driven pumps powered by a small bleed-off combustor, and so on. Each module in this sub-package implements one topology and conforms to the [`FeedSystem`][machwave.models.feed_systems.base.FeedSystem] contract so the simulation loop can treat them interchangeably.

## Available cycles

- [`StackedTankPressureFedFeedSystem`](#stackedtankpressurefedfeedsystem) — Pressure-fed engine with the oxidizer tank stacked directly above a piston-separated fuel tank. Tank pressure provides both propellants' driving head.
- [`SingleLinePressureFedFeedSystem`](#singlelinepressurefedfeedsystem) — Pressure-fed engine feeding one line, which the tank pressurizes itself. The one-line case of the contract: an oxidizer-only hybrid feed or a monoliquid.

The cycle reads tank state through the [`PropellantLine`][machwave.models.feed_systems.lines.PropellantLine] instances it was constructed with, and combines that state with any [component specs](components.md) it owns to say what reaches the injector face. The simulation step lives in [`BiliquidEngineState.run_timestep`][machwave.simulation.biliquid.states.BiliquidEngineState.run_timestep], which calls `get_inlet_states` once per integration step and hands the results to the [`Injector`][machwave.models.thrust_chamber.injector.Injector] at each chamber pressure the solver tries.

---

## `StackedTankPressureFedFeedSystem`

A pressure-fed engine whose propellant tanks are arranged as a single vertical stack separated by a piston. The tank at the top of the stack, `pressurizing_line`, pressurises every propellant: directly for its own line, and through the piston for every line below it. Pressure loss across the piston is captured by `piston_loss`, and each feedline loses what its own [`FeedlineResistance`][machwave.models.feed_systems.lines.FeedlineResistance] takes at the line flow.

**Construction**

The two-line case a biliquid engine runs on has a convenience constructor, which names the lines `"oxidizer"` and `"fuel"`:

```python
from machwave.models.feed_systems import (
    FeedlineResistance,
    StackedTankPressureFedFeedSystem,
)
from machwave.models.feed_systems.tank import Tank

feed_system = StackedTankPressureFedFeedSystem.from_oxidizer_and_fuel(
    oxidizer_tank=Tank("N2O", volume=0.010, temperature=298.0, initial_fluid_mass=5.0),
    fuel_tank=Tank("Ethanol", volume=0.008, temperature=298.0, initial_fluid_mass=3.0),
    piston_loss=0.0,  # Pa
    # 2 bar at 0.83 kg/s of liquid N2O through a 10.9 mm bore
    oxidizer_line_resistance=FeedlineResistance.from_design_point(
        pressure_drop=2e5, mass_flow=0.83, density=725.0, flow_area=9.37e-5
    ),
    # or the loss coefficient of the run and its fittings, referred to the bore
    fuel_line_resistance=FeedlineResistance(loss_coefficient=8.0, flow_area=9.37e-5),
)
```

Any other propellant count is built from the lines themselves — here a triliquid with a diluent below the piston:

```python
from machwave.models.feed_systems import PropellantLine, StackedTankPressureFedFeedSystem
from machwave.models.propellants import ComponentRole

feed_system = StackedTankPressureFedFeedSystem(
    lines=[
        PropellantLine(
            name="oxidizer", role=ComponentRole.OXIDIZER, tank=oxidizer_tank,
            resistance=oxidizer_resistance,
        ),
        PropellantLine(
            name="fuel", role=ComponentRole.FUEL, tank=fuel_tank,
            resistance=fuel_resistance,
        ),
        PropellantLine(name="diluent", role=ComponentRole.ADDITIVE, tank=diluent_tank),
    ],
    pressurizing_line="oxidizer",
    piston_loss=1e5,
)
```

**Mass-flow model.** The feed system supplies the state at the head of every feedline: the pressurizing tank pressure for its own line, and that pressure less `piston_loss` for every line below the piston. The piston loss is seal friction and holds at any flow. Density comes from [`Tank.get_density`][machwave.models.feed_systems.tank.Tank.get_density].

The feedline itself loses pressure with the square of its flow,

$$
\Delta P_{line} = K \frac{\dot{m}^2}{2 \rho A^2},
$$

so the injector element sees $P_{head} - \Delta P_{line}(\dot{m})$ and its flow is the root of $\dot{m} = f_{inj}(P_{head} - \Delta P_{line}(\dot{m}), P_c)$. [`get_line_mass_flow`][machwave.simulation.biliquid.states.get_line_mass_flow] brackets it on $[0, f_{inj}(P_{head}, P_c)]$ and solves it per line at every chamber pressure the integrator tries. The injector picks the orifice model per line from its [`MassFlowModel`][machwave.models.thrust_chamber.injector.MassFlowModel]. A line with no resistance loses nothing.

`line_losses` and `from_oxidizer_and_fuel`'s `oxidizer_line_loss` and `fuel_line_loss` still take a fixed pressure drop off the feedline head, whatever the flow, but are deprecated in favor of a `FeedlineResistance` on each line.

---

## `SingleLinePressureFedFeedSystem`

One propellant line, pressurized by its own tank: a self-pressurized propellant rides its vapor pressure while liquid remains, then blows down on the real-gas equation of state. The line's [`FeedlineResistance`][machwave.models.feed_systems.lines.FeedlineResistance] then takes its flow-dependent loss on the way to the injector, as for the stacked tank. An empty tank delivers nothing, which stops the flow at the injector element.

**Construction**

```python
from machwave.models.feed_systems import (
    FeedlineResistance,
    SingleLinePressureFedFeedSystem,
)
from machwave.models.feed_systems.tank import Tank

feed_system = SingleLinePressureFedFeedSystem.from_oxidizer_tank(
    oxidizer_tank=Tank("N2O", volume=0.010, temperature=298.0, initial_fluid_mass=5.0),
    line_resistance=FeedlineResistance(loss_coefficient=8.0, flow_area=9.37e-5),
)
```

The fixed `line_loss` is deprecated in favor of `line_resistance`; while it lasts, `get_inlet_pressures` still takes it off the tank pressure.

A monoliquid names its own line and role instead, through the `PropellantLine` constructor.

---

::: machwave.models.feed_systems.cycles
