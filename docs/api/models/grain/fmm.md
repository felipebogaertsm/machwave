# models.grain.fmm

Fast Marching Method (FMM) base classes for grain geometries with complex cross-sections that cannot be described analytically. FMM operates on a 2D (or 3D) distance map to compute burn area and port area as the flame front regresses inward.

- `FMMGrainSegment` — Base class providing the distance-map regression logic.
- `FMMGrainSegment2D` — Constant cross-section FMM geometries (Star, D-grain).
- `FMMGrainSegment3D` — Varying cross-section FMM geometries (WagonWheel).
- `FMMSTLGrainSegment` — Import arbitrary grain geometry from an STL mesh file.

Used internally by the concrete geometry classes in [geometries](geometries.md).

::: machwave.models.grain.fmm
