# Grain regression

Applies to `machwave/models/grain/`.

## Resolution

- Fast marching results depend strongly on `grid_resolution`. Total impulse of a
  three-dimensional finocyl rises with resolution and has not converged at 100; a coarse
  grid is not a usable approximation (at 20 the total impulse is about 63 % low).
- `MINIMUM_GRID_RESOLUTION` and `DEFAULT_GRID_RESOLUTION` stay at 100
  (`machwave/models/grain/fmm/base.py`). Never lower them for speed.
- To speed up a fast marching test, shorten the grain (fewer axial layers) instead of
  coarsening the cross-section.

## Geometry changes

- A change to burn area, perimeter or volume extraction is checked against an independent
  geometric reference before merging: a closed-form area for simple ports (circle, annulus,
  BATES segment) or a CAD measurement for complex ones.
- Check both two-dimensional and three-dimensional paths, and both odd and even grid
  sizes, when the change touches contour tracing or masking.
- Inhibited faces and casing walls never count as burning surface.
- Analytical geometries (BATES) and fast marching geometries must agree on the same port
  shape within the discretization error of the fast marching grid.
