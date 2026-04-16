# models.grain.geometries

Concrete grain segment geometries, both analytical and FMM-based.

**2D (constant cross-section):**

- `BatesSegment` — Standard cylindrical grain with axial core (the most common hobby/amateur geometry).
- `TubularSegment` — Thin-walled tube, burns from inner and/or outer surfaces.
- `RodAndTubeSegment` — Central rod surrounded by an outer tubular section.
- `MultiPortGrainSegment` — Multiple circular ports arranged radially in the cross-section.
- `StarGrainSegment` — Star-shaped port (FMM-based). Configurable point count, length, and width.
- `DGrainSegment` — D-shaped slot port (FMM-based).

**3D (varying cross-section):**

- `ConicalGrainSegment` — Linearly tapered core from upper to lower diameter.
- `WagonWheelSegment` — Complex multi-spoke geometry (FMM-based).

All segments implement the `GrainSegment` interface and can be mixed within a single `Grain`.

::: machwave.models.grain.geometries
