# Fast Marching Method (FMM) grain geometries

This module implements numerical propellant grain regression using the Fast Marching
Method (FMM).

Grain regression analysis can be done using analytical or numerical methods. Analytical
solutions are typically faster to solve and more exact, at the cost of complex
modeling. Machwave uses the numerical Fast Marching Method (FMM) when it is hard or
impractical to model a geometry analytically, such as a star or finocyl.

## Regression Analysis with FMM

Here is a step by step flow of how it works:

### 1. Model the geometry

1. The geometry is mapped onto a 2D or 3D grid (`get_initial_face_map`). Each grid
   element is assigned a value: `1` means solid propellant; `0` means void. This method
   needs to be implemented by every geometry.

   Example initial face map (simple circular port):

   ```
   [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
   ```

2. The circular outer boundary is enforced with a mask (`get_mask`). Elements outside
   the unit-radius circle in normalized coordinates are considered outside the grain
   (`-1`).

   Example mask (True = outside grain boundary):

   ```
   [[ T,  T,  T,  T,  T,  T,  T,  T,  T,  T,  T,  T],
    [ T,  T,  T,  F,  F,  F,  F,  F,  F,  T,  T,  T],
    [ T,  T,  F,  F,  F,  F,  F,  F,  F,  F,  T,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  F,  F,  F,  F,  F,  F,  F,  F,  F,  F,  T],
    [ T,  T,  F,  F,  F,  F,  F,  F,  F,  F,  T,  T],
    [ T,  T,  T,  F,  F,  F,  F,  F,  F,  T,  T,  T],
    [ T,  T,  T,  T,  T,  T,  T,  T,  T,  T,  T,  T]]
   ```

### 2. Compute the regression distance map

1. The initial face map is combined with the circular mask (`get_masked_face`) to
   create a `MaskedArray`. This ensures FMM only operates within the valid grain
   region.

   Example masked face (-- = masked):

   ```
   [[ --,  --,  --,  --,  --,  --,  --,  --,  --,  --,  --,  --],
    [ --,  --,  --,   1,   1,   1,   1,   1,   1,  --,  --,  --],
    [ --,  --,   1,   1,   1,   1,   1,   1,   1,   1,  --,  --],
    [ --,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,  --],
    [ --,   1,   1,   1,   1,   0,   0,   1,   1,   1,   1,  --],
    [ --,   1,   1,   1,   0,   0,   0,   0,   1,   1,   1,  --],
    [ --,   1,   1,   1,   0,   0,   0,   0,   1,   1,   1,  --],
    [ --,   1,   1,   1,   1,   0,   0,   1,   1,   1,   1,  --],
    [ --,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,  --],
    [ --,  --,   1,   1,   1,   1,   1,   1,   1,   1,  --,  --],
    [ --,  --,  --,   1,   1,   1,   1,   1,   1,  --,  --,  --],
    [ --,  --,  --,  --,  --,  --,  --,  --,  --,  --,  --,  --]]
   ```

2. The Fast Marching Method is applied (`get_regression_map`) using `skfmm.distance` to
   calculate the distance from each solid propellant point to the nearest void. The
   cell size is set to `1/map_dim` for proper scaling.

   Example regression map (normalized distances):

   ```
   [[----, ----, ----, ----, ----, ----, ----, ----, ----, ----, ----, ----],
    [----, ----, ----, 0.54, 0.46, 0.42, 0.42, 0.46, 0.54, ----, ----, ----],
    [----, ----, 0.52, 0.41, 0.32, 0.26, 0.26, 0.32, 0.41, 0.52, ----, ----],
    [----, 0.54, 0.41, 0.29, 0.19, 0.11, 0.11, 0.19, 0.29, 0.41, 0.54, ----],
    [----, 0.46, 0.32, 0.19, 0.08, 0.00, 0.00, 0.08, 0.19, 0.32, 0.46, ----],
    [----, 0.42, 0.26, 0.11, 0.00, 0.00, 0.00, 0.00, 0.11, 0.26, 0.42, ----],
    [----, 0.42, 0.26, 0.11, 0.00, 0.00, 0.00, 0.00, 0.11, 0.26, 0.42, ----],
    [----, 0.46, 0.32, 0.19, 0.08, 0.00, 0.00, 0.08, 0.19, 0.32, 0.46, ----],
    [----, 0.54, 0.41, 0.29, 0.19, 0.11, 0.11, 0.19, 0.29, 0.41, 0.54, ----],
    [----, ----, 0.52, 0.41, 0.32, 0.26, 0.26, 0.32, 0.41, 0.52, ----, ----],
    [----, ----, ----, 0.54, 0.46, 0.42, 0.42, 0.46, 0.54, ----, ----, ----],
    [----, ----, ----, ----, ----, ----, ----, ----, ----, ----, ----, ----]]
   ```

3. The web thickness is determined (`get_web_thickness`) by finding the maximum value
   in the regression map and denormalizing it to meters.

### 3. Calculate geometry at any burn distance

1. For a given `web_distance`, the regression state is queried (`get_face_map`).
   Points where `regression_map > web_distance_normalized` contain solid propellant
   (value = 1), burned away points have value = 0, and masked points remain -1.

   Example face map at web_distance = 0.15 (normalized):

   ```
   [[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1,  1,  1,  1,  1,  1,  1, -1, -1, -1],
    [-1, -1,  1,  1,  1,  1,  1,  1,  1,  1, -1, -1],
    [-1,  1,  1,  1,  1,  0,  0,  1,  1,  1,  1, -1],
    [-1,  1,  1,  1,  0,  0,  0,  0,  1,  1,  1, -1],
    [-1,  1,  1,  0,  0,  0,  0,  0,  0,  1,  1, -1],
    [-1,  1,  1,  0,  0,  0,  0,  0,  0,  1,  1, -1],
    [-1,  1,  1,  1,  0,  0,  0,  0,  1,  1,  1, -1],
    [-1,  1,  1,  1,  1,  0,  0,  1,  1,  1,  1, -1],
    [-1, -1,  1,  1,  1,  1,  1,  1,  1,  1, -1, -1],
    [-1, -1, -1,  1,  1,  1,  1,  1,  1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
   ```

   Example face map at web_distance = 0.35 (normalized):

   ```
   [[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1,  1,  1,  1,  1,  1,  1, -1, -1, -1],
    [-1, -1,  1,  1,  0,  0,  0,  0,  1,  1, -1, -1],
    [-1,  1,  1,  0,  0,  0,  0,  0,  0,  1,  1, -1],
    [-1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1, -1],
    [-1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1, -1],
    [-1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1, -1],
    [-1,  1,  0,  0,  0,  0,  0,  0,  0,  0,  1, -1],
    [-1,  1,  1,  0,  0,  0,  0,  0,  0,  1,  1, -1],
    [-1, -1,  1,  1,  0,  0,  0,  0,  1,  1, -1, -1],
    [-1, -1, -1,  1,  1,  1,  1,  1,  1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
   ```

2. Contours are extracted (`get_contours`) at the regression threshold to get the
   burning surface boundaries.

### 4. Compute ballistic properties

1. Interpolation functions are built (`get_face_area_interp_func`,
   `get_burn_area_interp_func`) by sorting regression map values and applying smoothing
   (Savitzky-Golay filter).
2. Face area is calculated (`get_face_area`) using the interpolation function.
3. Port area is calculated (`get_port_area`) by subtracting face area from total
   circular area.
4. Burn area is calculated (`get_burn_area`) from the perimeter of burning contours.

## References

- Sethian, "Fast Marching Method" explanation:
  https://math.berkeley.edu/~sethian/2006/Explanations/fast_marching_explain.html
