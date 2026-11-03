# common

Value objects and helpers shared across the library, belonging to no single
model package.

- `FluidState` — A fluid at a thermodynamic state point: fluid name, pressure, temperature, and density. What a feed system hands the injector, so neither package has to import the other.
- `DryMassProperties` — Mass, center of gravity, and inertia tensor of a device's dry structure.
- `AxisymmetricMassProperties` — Mass, axial center of gravity, and axial and transverse moments of inertia of a body symmetric about the thrust axis, combined across coaxial bodies with the parallel axis theorem.
- `require()` — Imports an optional dependency, raising `MissingOptionalDependencyError` naming the packaging extra that ships it.

::: machwave.common.fluid_state

::: machwave.common.mass_properties

::: machwave.common.extras
