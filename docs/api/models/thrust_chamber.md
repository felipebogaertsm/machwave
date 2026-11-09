# models.thrust_chamber

Thrust chamber assembly and sub-components.

- `Nozzle` — Conical nozzle defined by throat diameter, expansion ratio, and divergent half-angle. Computes throat area and outlet diameter.
- `CombustionChamber` — Cylindrical chamber defined by its inner diameter and internal length. Provides the internal volume. The inner diameter is the chamber bore, measured inside the liner if there is one, or at the casing wall if there is none. Inhibitors belong to the grain and are not subtracted: an inhibitor sleeve's annulus counts as free chamber volume.
- `InjectorElement` — The orifices one propellant line flows through, characterized by a discharge coefficient, a flow area and a factor on Dyer's non-equilibrium parameter. `get_mass_flow(*, inlet, chamber_pressure)` is Dyer's non-homogeneous non-equilibrium flow, the incompressible orifice flow where nothing flashes and its blend with the homogeneous equilibrium flow where the liquid is near saturation; see [Injector Flow](../../explanations/injector_flow.md).
- `Injector` — One `InjectorElement` per propellant line, keyed by the feed system's line names. `get_mass_flows(*, inlet_states, chamber_pressure)` takes the inlet state of every line and returns the flow of every line. Each element is fed a [`FluidState`][machwave.common.fluid_state.FluidState] — fluid name, pressure, temperature, and density at the injector face — and is a pure function of it. An element stops flowing once the chamber has caught up with its inlet. In a biliquid simulation the inlet is the feedline head state less the line's flow-dependent loss, which [`get_line_mass_flow`][machwave.simulation.biliquid.states.get_line_mass_flow] solves together with the element flow.
- `SolidMotorThrustChamber` — Bundles nozzle + chamber + the distance from nozzle exit to grain port.
- `BiliquidEngineThrustChamber` — Bundles nozzle + chamber + injector.

::: machwave.models.thrust_chamber
