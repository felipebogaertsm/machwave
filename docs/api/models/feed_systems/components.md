# models.feed_systems.components

Static, immutable descriptions of the physical components a feed-system cycle is built from. The classes in this sub-package do not contain integration state and never mutate during a simulation. Cycle implementations in [`machwave.models.feed_systems.cycles`](cycles.md) combine these specifications with the live tank state and chamber conditions to compute mass flow, head rise, and shaft power. The cycles that do so — electric-pump, gas-generator, expander and staged-combustion — are not implemented yet: the two pressure-fed cycles available today read none of these specifications.

- `PumpSpec` — A propellant pump at its design point: isentropic efficiency, pressure rise, volumetric flow, and shaft speed.
- `TurbineSpec` — A turbine at its design point: isentropic efficiency, pressure ratio, inlet temperature, and mass flow.
- `GasGeneratorSpec` — The gas generator driving the turbine in a gas-generator cycle, or the preburner in a staged-combustion cycle: mixture ratio, chamber pressure, gas temperature, and mass flow.
- `RegenerativeJacketSpec` — A regenerative cooling jacket wrapping the combustion chamber and nozzle: pressure drop, coolant temperature rise, and heat pickup.

Every spec is a frozen, keyword-only dataclass with `__post_init__` validation; construction with an out-of-range value raises `ValueError`. Each field, its units and its bounds are documented on the class below.

::: machwave.models.feed_systems.components
