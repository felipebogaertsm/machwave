# models.thrust_chamber

Thrust chamber assembly and sub-components.

- `Nozzle` — Conical nozzle defined by throat diameter, expansion ratio, convergent/divergent half-angles, and boundary-layer loss coefficients (`c_1`, `c_2`). Computes throat area and outlet diameter.
- `CombustionChamber` — Cylindrical casing with thermal liner. Provides internal volume from casing dimensions and liner thickness.
- `BipropellantInjector` — Injector for biliquid engines, characterized by discharge coefficients and orifice areas for oxidizer and fuel.
- `SolidMotorThrustChamber` — Bundles nozzle + chamber + the distance from nozzle exit to grain port.
- `BiliquidEngineThrustChamber` — Bundles nozzle + chamber + injector.

::: machwave.models.thrust_chamber
