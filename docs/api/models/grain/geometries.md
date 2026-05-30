# models.grain.geometries

Concrete grain segment geometries, both analytical and FMM-based.

**2D (constant cross-section):**

- `BatesSegment` — Cylindrical grain with an axial core, the most common amateur geometry (analytical).
- `RodAndTubeGrainSegment` — Central rod surrounded by an outer tube (FMM-based).
- `MultiPortGrainSegment` — Multiple circular ports arranged radially in the cross-section (FMM-based).
- `StarGrainSegment` — Star-shaped port with configurable point count, length, and width (FMM-based).
- `DGrainSegment` — D-shaped slot port (FMM-based).
- `WagonWheelGrainSegment` — Multi-spoke geometry with a central core and radial ports (FMM-based).

**3D (varying cross-section):**

- `ConicalGrainSegment` — Linearly tapered core from upper to lower diameter.
- `FinocylGrainSegment` — Central circular bore with radial fins over a partial axial section (FMM-based).

All segments implement the `GrainSegment` interface and can be mixed within a single `Grain`.

::: machwave.models.grain.geometries
