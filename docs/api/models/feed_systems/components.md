# models.feed_systems.components

Static, immutable descriptions of the physical components a feed-system cycle is built from. The classes in this sub-package do not contain integration state and never mutate during a simulation — they sit alongside propellant definitions as part of the engine *configuration*. Cycle implementations in [`machwave.models.feed_systems.cycles`](cycles.md) read these specifications and combine them with the live tank state and chamber conditions to compute mass flow, head rise, and shaft power.

Every spec is implemented as a `@dataclass(frozen=True, kw_only=True)` with `__post_init__` validation, mirroring the convention used by [`ThermochemicalProperties`][machwave.models.propellants.properties.ThermochemicalProperties]. Construction with an out-of-range value raises `ValueError` at the call site rather than producing nonsensical numbers downstream.

Specs that carry property *curves* (e.g. pump head versus volumetric flow, turbine efficiency versus pressure ratio) wrap their tabulated data in [`machwave.core.interpolation.BoundedCubicSpline`](../../core/interpolation.md), which raises rather than extrapolating outside the calibrated knots.

## When you need which spec

| Cycle topology | Needs | Why |
| --- | --- | --- |
| Pressure-fed (stacked, regulated, blowdown) | nothing in this package | The injector orifice equation and tank pressure are sufficient. |
| Electric-pump | [`PumpSpec`](#pumpspec) | Each pump still needs design-point data even though the drive is electric, because head rise is interpolated from the pump curve. |
| Gas-generator | [`PumpSpec`](#pumpspec), [`TurbineSpec`](#turbinespec), [`GasGeneratorSpec`](#gasgeneratorspec) | The gas generator burns a small fraction of the propellants to drive the turbine, which in turn drives the pumps. |
| Expander | [`PumpSpec`](#pumpspec), [`TurbineSpec`](#turbinespec), [`RegenerativeJacketSpec`](#regenerativejacketspec) | Heat absorbed by the coolant in the jacket vaporises one propellant; that vapor drives the turbine. |
| Staged combustion | [`PumpSpec`](#pumpspec), [`TurbineSpec`](#turbinespec), [`GasGeneratorSpec`](#gasgeneratorspec) (as preburner), [`RegenerativeJacketSpec`](#regenerativejacketspec) | The full pre-combusted flow is routed through the turbine and then into the main chamber. |

See Sutton & Biblarz, *Rocket Propulsion Elements* (Wiley, 2017), chapter 10, and Huzel & Huang, *Modern Engineering for Design of Liquid-Propellant Rocket Engines* (AIAA, 1992), chapter 6, for the underlying engine-cycle theory these specs describe.

---

## `PumpSpec`

Captures a propellant pump at its design point. The fields are deliberately limited to what a cycle integrator needs to evaluate head rise and shaft power from a single operating point — anything that varies with operating condition (head-flow curve, NPSH margin) belongs in a [`BoundedCubicSpline`](../../core/interpolation.md) and stored alongside the spec by the cycle that owns it.

| Field | Units | Constraint |
| --- | --- | --- |
| `name` | — | Free-form identifier used in logs and reports. |
| `isentropic_efficiency` | — | $\eta_p \in (0, 1]$ |
| `pressure_rise` | Pa | Strictly positive |
| `volumetric_flow_design` | m³/s | Strictly positive |
| `shaft_speed_design` | rad/s | Strictly positive |

Shaft power at the design point follows directly from the fields, assuming an incompressible working fluid:

\[
\dot{W}_{\text{shaft}} = \frac{\dot{V} \cdot \Delta P}{\eta_p}
\]

---

## `TurbineSpec`

Captures a turbine at its design point. Cycle integrators evaluate the specific work extracted from the working fluid using the inlet temperature and pressure ratio, then deliver the resulting shaft power to the coupled pump(s).

| Field | Units | Constraint |
| --- | --- | --- |
| `name` | — | Free-form identifier. |
| `isentropic_efficiency` | — | $\eta_t \in (0, 1]$ |
| `pressure_ratio` | — | $\pi_t > 1$ |
| `inlet_temperature_design` | K | Strictly positive |
| `mass_flow_design` | kg/s | Strictly positive |

Isentropic specific work for a perfect gas across the turbine:

\[
w_t = c_p \cdot T_{t,\text{in}} \cdot \left[1 - \pi_t^{-(\gamma - 1)/\gamma}\right] \cdot \eta_t
\]

`mass_flow_design` is recorded for sizing checks: the cycle solver verifies that the working-fluid mass flow it computes (for a gas generator, the burned fraction; for an expander, the regen flow) stays close to the design point used to specify the turbine.

---

## `GasGeneratorSpec`

Describes the gas generator that drives the turbine in a gas-generator-cycle engine or the preburner in a staged-combustion engine. The defining design choice is the operating mixture ratio, which is held well off-stoichiometric so the combustion-product temperature stays below uncooled turbine-blade metal limits.

| Field | Units | Constraint |
| --- | --- | --- |
| `name` | — | Free-form identifier. |
| `mixture_ratio` | — | Strictly positive (oxidizer/fuel mass ratio). |
| `chamber_pressure` | Pa | Strictly positive |
| `gas_temperature` | K | Must lie in `[GAS_TEMPERATURE_MINIMUM_KELVIN, GAS_TEMPERATURE_MAXIMUM_KELVIN]` (300 K – 1500 K). |
| `mass_flow` | kg/s | Strictly positive |

The temperature bounds exist to catch unit-confusion bugs and configurations that would silently melt a real turbine — they are intentionally wider than any well-designed gas generator would run, but narrow enough to reject obvious mistakes.

---

## `RegenerativeJacketSpec`

Describes a regenerative cooling jacket wrapping the combustion chamber and nozzle. One propellant — typically the fuel, sometimes the oxidizer in oxidizer-rich cycles — is routed through cooling passages to absorb heat from the chamber walls before injection. The jacket therefore acts simultaneously as a heat exchanger and a pressure-loss component in the feed train.

| Field | Units | Constraint |
| --- | --- | --- |
| `name` | — | Free-form identifier. |
| `pressure_drop` | Pa | Non-negative |
| `coolant_temperature_rise` | K | Strictly positive |
| `heat_pickup` | W | Non-negative |

`heat_pickup` and `coolant_temperature_rise` are not independent — once a coolant mass flow is fixed they are linked by $\dot{Q} = \dot{m} \cdot c_p \cdot \Delta T$. Both are stored because the cycle solver needs `heat_pickup` to compute the turbine inlet enthalpy in an expander cycle, and `coolant_temperature_rise` to verify the jacket is not over-pushed thermally.

---

::: machwave.models.feed_systems.components
