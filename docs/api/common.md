# common

Value objects and helpers shared across the library, belonging to no single
model package.

- `FluidState` — A fluid at a thermodynamic state point: fluid name, pressure, temperature, and density. What a feed system hands the injector, so neither package has to import the other.
- `DryMassProperties` — Mass, center of gravity, and inertia tensor of a device's dry structure.
- Array manipulation helpers and a `@timing` decorator for profiling.

::: machwave.common.fluid_state

::: machwave.common.mass_properties

::: machwave.common.arrays

::: machwave.common.decorators

::: machwave.common.objects
