# models.grain

Grain geometry and regression model. The `Grain` class is a container that holds one or more `GrainSegment` instances (potentially of different geometries) and aggregates burn area, propellant mass, CoG, and moment of inertia across all segments at any web regression distance.

Each segment exposes a common interface: `get_burn_area()`, `get_port_area()`, `get_volume()`, `get_web_thickness()`, `get_center_of_gravity()`, and `get_moment_of_inertia()`. Surface inhibition is controlled per-segment via `InhibitedSurfaces`.

Submodules:

- [geometries](grain/geometries.md) — Concrete grain segment types (BATES, tubular, star, D-grain, conical, etc.)
- [fmm](grain/fmm.md) — Fast Marching Method base classes for complex cross-sections

::: machwave.models.grain
