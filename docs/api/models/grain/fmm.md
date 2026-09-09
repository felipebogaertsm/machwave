# models.grain.fmm

Fast Marching Method (FMM) base classes for grain geometries whose cross-section cannot be described analytically. The burning surface at any web distance is read off a single distance map of the initial port, solved with scikit-fmm.

!!! note "Requires the `fmm` extra"
    `pip install machwave[fmm]`. Constructing any FMM segment without it raises an `ImportError` naming that command. `BatesSegment` is analytical and needs no extra.

- `FMMGrainSegment` — Shared regression logic: builds the distance map and derives web thickness, the regressed face map, and port and burn area from it.
- `FMMGrainSegment2D` — Constant cross-section geometries (Star, D-grain, wagon-wheel, multi-port, rod-and-tube). Burn area is the core perimeter (a single contour of the distance map) times the grain length, plus any exposed end faces.
- `FMMGrainSegment3D` — Axially varying cross-section geometries (Conical, Finocyl). The port is a stack of axial slices through a 3D distance map; burn area is the marching-cubes area of the regressing iso-surface, and port area is read from a chosen slice.
- `FMMSTLGrainSegment` — Arbitrary grain geometry imported from an STL mesh file.

Used internally by the concrete geometry classes in [geometries](geometries.md).

::: machwave.models.grain.fmm
