# models.thrust_chamber

Thrust chamber assembly and sub-components.

- `Nozzle` — Conical nozzle defined by throat diameter, expansion ratio, and convergent/divergent half-angles. Computes throat area and outlet diameter.
- `CombustionChamber` — Cylindrical casing with thermal liner. Provides internal volume from casing dimensions and liner thickness.
- `BipropellantInjector` — Injector for biliquid engines, characterized by discharge coefficients, orifice areas, and a per-side `MassFlowModel` for the oxidizer and fuel sides. Owns the orifice mass-flow dispatch: `get_mass_flow_ox(*, tank, pressure_upstream, chamber_pressure, fluid_mass)` and `get_mass_flow_fuel(*, tank, pressure_upstream, chamber_pressure, fluid_mass)`. Feed systems delegate to these methods.
- `MassFlowModel` — Enum selecting the orifice flow model. `SPI` (single-phase incompressible) for subcooled liquid propellants; `HEM` (homogeneous-equilibrium two-phase) for self-pressurized propellants such as nitrous oxide, where flow can choke on the two-phase sound speed.
- `SolidMotorThrustChamber` — Bundles nozzle + chamber + the distance from nozzle exit to grain port.
- `BiliquidEngineThrustChamber` — Bundles nozzle + chamber + injector.
- `DryMassProperties` — Optional dry mass, center of gravity, and principal moments of inertia bundle passed to a thrust chamber; consumed only by the RocketPy trajectory adapter, not by internal ballistics.

::: machwave.models.thrust_chamber
