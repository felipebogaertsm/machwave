# models.thrust_chamber

Thrust chamber assembly and sub-components.

- `Nozzle` — Conical nozzle defined by throat diameter, expansion ratio, and convergent/divergent half-angles. Computes throat area and outlet diameter.
- `CombustionChamber` — Cylindrical casing with thermal liner. Provides internal volume from casing dimensions and liner thickness.
- `InjectorElement` — The orifices one propellant line flows through, characterized by a discharge coefficient, a flow area, and a `MassFlowModel`. Owns the orifice mass-flow dispatch: `get_mass_flow(*, inlet, chamber_pressure)`.
- `Injector` — One `InjectorElement` per propellant line, keyed by the feed system's line names. `get_mass_flows(*, inlet_states, chamber_pressure)` takes the inlet state of every line and returns the flow of every line. Each element is fed a [`FluidState`][machwave.common.fluid_state.FluidState] — fluid name, pressure, temperature, and density at the injector face — and is a pure function of it. An element stops flowing once the chamber has caught up with its inlet.
- `MassFlowModel` — Enum selecting the orifice flow model. `SPI` (single-phase incompressible) for subcooled liquid propellants; `HEM` (homogeneous-equilibrium two-phase) for self-pressurized propellants such as nitrous oxide, where flow can choke on the two-phase sound speed.
- `SolidMotorThrustChamber` — Bundles nozzle + chamber + the distance from nozzle exit to grain port.
- `BiliquidEngineThrustChamber` — Bundles nozzle + chamber + injector.

::: machwave.models.thrust_chamber
