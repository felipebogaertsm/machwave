# models.propellants.categories

Propellant type classes.

- `SolidPropellant` — Defined by component mass fractions, pre-computed or CEA-evaluated thermochemical properties, and a `burn_rate_map` encoding St. Robert’s law coefficients ($r = a \cdot P_0^n$) across pressure ranges. Call `get_burn_rate(P_0)` to obtain instantaneous regression rate.
- `BiliquidPropellant` — Defined by exactly two components (oxidizer + fuel) and an O/F mass ratio. Thermochemical properties are evaluated at the specified O/F.

    By default each component's `name` is looked up in RocketCEA's built-in cards and its other fields are ignored; `"N2O"` there is the ideal gas at 298.15 K. A component with `custom_card=True` is sent to CEA as its own reactant card instead. `saturated_liquid_nitrous_oxide(T)` builds one for self-pressurized nitrous oxide at the tank temperature.

Both extend the `Propellant` base class and implement `evaluate(chamber_pressure, expansion_ratio, mixture_ratio=None)` to return a `ThermochemicalProperties` dataclass. A `SolidPropellant` carrying pre-computed properties returns them directly and needs no thermochemistry solver; every other path evaluates through CEA and needs the `cea` extra. The optional `mixture_ratio` overrides the propellant's stored ratio per-call — `BiliquidEngineState` uses this to feed the live $\dot{m}_{ox} / \dot{m}_{fuel}$ each step.

::: machwave.models.propellants.categories
