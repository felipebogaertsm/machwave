# models.thrust_chamber

Thrust chamber assembly and sub-components.

- `Nozzle` — Conical nozzle defined by throat diameter, expansion ratio, and convergent/divergent half-angles. Computes throat area and outlet diameter.
- `CombustionChamber` — Cylindrical casing with thermal liner. Provides internal volume from casing dimensions and liner thickness.
- `BipropellantInjector` — Injector for biliquid engines, characterized by discharge coefficients, orifice areas, and a per-side `MassFlowModel` for the oxidizer and fuel sides. Owns the orifice mass-flow dispatch: `get_mass_flow_ox(*, inlet, chamber_pressure)` and `get_mass_flow_fuel(*, inlet, chamber_pressure)`.
Each side of the injector is fed a [`FluidState`][machwave.common.fluid_state.FluidState] — fluid name, pressure, temperature, and density at the injector face. The feed system evaluates it and the injector consumes it, so anything upstream of the face — tank state, feedline and piston losses, a regenerative jacket, a pump — is the feed system's to account for, and the injector never sees a tank.
- `MassFlowModel` — Enum selecting the orifice flow model. `SPI` (single-phase incompressible) for subcooled liquid propellants; `HEM` (homogeneous-equilibrium two-phase) for self-pressurized propellants such as nitrous oxide, where flow can choke on the two-phase sound speed.
- `SolidMotorThrustChamber` — Bundles nozzle + chamber + the distance from nozzle exit to grain port.
- `BiliquidEngineThrustChamber` — Bundles nozzle + chamber + injector.

## Center Of Gravity Frames

Machwave measures axial positions along three nested frames, all with positive x
pointing toward the bulkhead:

| Frame | Origin | Where it appears |
| --- | --- | --- |
| Grain segment | That segment's own port face, closest to the nozzle | `GrainSegment.get_center_of_gravity` |
| Grain | The grain port face, closest to the nozzle | `Grain.get_center_of_gravity` |
| Motor | The nozzle exit plane | `SolidSimulationResult.propellant_cog`, `DryMassProperties.center_of_gravity_coordinate` |

`nozzle_exit_to_grain_port_distance` on `SolidMotorThrustChamber` is what carries
the grain frame into the motor frame. A segment origin is the initial position of
its port face and stays fixed as that face regresses.

::: machwave.models.thrust_chamber
