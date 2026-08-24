# FMM module naming improvement plan

A plan to give every function, method, and variable in the Fast Marching Method
(FMM) grain-regression module a self-describing name, grounded in the standard
vocabulary of the relevant fields rather than ad-hoc abbreviations.

Scope: `machwave/models/grain/fmm/` — `base.py`, `_2d.py`, `_3d.py`, `stl.py`,
`contours.py`.

## Why

The current names mix three sins that the literature on naming warns against:

- **Semantically empty names** — `get_maps`, `mask`, `maps`, `values`,
  `counts`, `valid`, `invalid`. They name a *type* ("a map", "some values")
  instead of the *thing* ("coordinate grids", "sorted regression distances").
- **Cryptic abbreviations** — `n_le`, `moi`, `I_axial`, `map_dim`, `map_dist`,
  `maskarr`. Unpronounceable, unsearchable, force mental translation.
- **Disinformation** — `map_dim` reads as *dimensionality* (2 vs 3) but means
  *grid points per axis*; `get_normalized_length` returns an integer **count**,
  not a length; `get_cell_size` returns a **normalized** spacing, not metres;
  a `map` parameter in `contours.py` shadows the `map` builtin.

## Guiding principles (from the literature)

| Principle | Source |
|---|---|
| Use intention-revealing names; avoid disinformation; make meaningful distinctions; use pronounceable, searchable names; avoid encodings and mental mapping | R. C. Martin, *Clean Code* (2008), ch. 2 |
| Name length should be proportional to scope; put computed-qualifiers (`Count`, `Total`, `Sum`, `Smoothed`) **last** | S. McConnell, *Code Complete* 2e (2004), ch. 11 |
| `snake_case`; predicates read as questions (`is_`, `has_`); `UPPER_CASE` constants | PEP 8; PEP 20 |
| Prefer the established term of the problem/solution domain over an invented one | Martin ch. 2; McConnell ch. 11 |

Domain vocabularies the names should draw from:

- **FMM / level-set / eikonal** — arrival-time field `T(x)`, distance field,
  signed distance function, front / zero level set, iso-contour, iso-surface,
  iso-level. (Sethian, *Level Set Methods and Fast Marching Methods*, 1999;
  Osher & Sethian, *JCP* 79, 1988; Osher & Fedkiw, 2003.)
- **Computational geometry** — voxel, voxelization, voxel/grid spacing,
  marching squares (2D) / marching cubes (3D), iso-surface extraction, mesh.
  (Lorensen & Cline, *SIGGRAPH* 1987; scikit-image / trimesh docs.)
- **Scientific computing** — grid points (`n`, `nx`, `ny`), grid spacing (`dx`),
  coordinate grids (meshgrid output), masked arrays (numpy.ma: `True` = excluded),
  interpolant. (NumPy / SciPy / scikit-fmm conventions.)
- **Solid-rocket internal ballistics** — web & web thickness, port / face /
  burn / core area, regression (burn-back), recession, inhibited surface,
  bore / core. (Sutton & Biblarz, *Rocket Propulsion Elements*.)

## Conventions adopted by this plan

1. **Preserve visibility.** A leading underscore is kept on rename — a private
   helper stays private. (Several names below keep a `_` the raw research dropped.)
2. **Coordinate-frame suffixes** for numeric arrays, spelled out (no
   abbreviations): `_grid` for normalized `[-1, 1]` grid coordinates ·
   `_denormalized` for values in metres (the output of `denormalize`) ·
   `_normalized` for dimensionless normalized values · `_relative` for
   coordinates relative to the centre of gravity.
3. **Grid vocabulary:** *grid resolution* = samples per axis (replaces `map_dim`);
   *grid spacing* = physical distance between samples (replaces `pitch` /
   `voxel_size`); *cell / pixel / voxel* = one grid element.
4. **Iso-level vocabulary** for level-set sampling: *iso level* (the threshold),
   *iso contour* (2D), *iso surface* (3D).
5. **Qualifier-last** for derived series: `face_area_smoothed`, `*_count`,
   `*_per_iso_level`.
6. **Keep established domain terms** even where an FMM-canon synonym exists:
   *web / web thickness*, *port / face / burn / core area*, *regression map*,
   *recession*, *inhibited surface*, *bore / core*. The value is in fixing the
   empty and cryptic names, not in re-labelling correct domain terms.

## Out of scope — the `GrainSegment` base contract

These names are defined or declared on `GrainSegment` / `GrainSegment2D` /
`GrainSegment3D` in `machwave/models/grain/base.py`. Renaming them ripples
across **every** geometry, the motor model, plots, and tests, so they are
**not** part of an FMM-only rename: `get_web_thickness`, `get_length`,
`get_port_area`, `get_burn_area`, `get_volume`, `get_face_area`, `get_core_area`,
`get_center_of_gravity`, `get_moment_of_inertia`, `get_mass`, `validate`,
and the parameters `web_distance`, `length`, `outer_diameter`, `density_ratio`,
`inhibited_surfaces`. They are already domain-standard and intention-revealing.

## Deliberately kept (considered and rejected)

- **`normalize` / `denormalize`** — a recognised mathematical pair; the inverse
  symmetry is itself information. A docstring noting "fraction of the radius"
  beats a verbose `to_normalized_half_diameter`.
- **The `face_map` terminology** — kept across `generate_initial_face_map`,
  `get_masked_face`, `get_face_map`, `get_empty_face_map`. "Face" is the correct
  grain-regression term (the burning cross-section); "occupancy grid" is robotics
  vocabulary that drifts from the FMM/SRM literature. `get_initial_face_map` was
  renamed to `generate_initial_face_map` (each geometry *constructs* it, so
  `generate` reads truer than `get`) — the widest-blast change, 81 references
  across 7 geometries, tests, docs, and the generated site. The other three keep
  their `get_` prefix; the cryptic *locals* around them are renamed below.
- **`get_regression_map` / `regression_map`** — the adversarial review favoured
  `get_arrival_time_field` on FMM-canon grounds (correct: under unit burn speed
  `T(x)` *is* the regression distance). **Decision: keep `regression_map`.**
  It is the term used throughout this module's `README.md` and the
  `docs/explanations` pages; renaming the code alone would split the vocabulary
  between code and docs. Instead, enrich the docstring: *"the FMM arrival-time
  field `T(x)`; under unit burn speed it equals the regression distance."*
- Short, clear locals in tight scopes: `inside`, `eroded`, `element_mass`,
  `total_mass`, `total_volume`, `volume_per_element`, `voxels`, `voxel_map`,
  `mesh`, `_resample_nearest`, `get_core_perimeter` (`core` is the project-wide
  term). The physics/coordinate abbreviations (`cog`, `moi`, `x_phys`, `x_rel`)
  were *not* kept — they are spelled out (`center_of_gravity`, `inertia_tensor`,
  `x_denormalized`, `x_relative`) per the no-abbreviation rule.

---

## Renames

Risk = blast radius: **Low** = within the FMM module · **Med** = also touched by
a geometry/test · **High** = touched by many geometries, tests, docs, and the
generated site. Counts come from a repo-wide usage trace.

### 1 · Grid & domain infrastructure (`base.py`, `_2d.py`, `_3d.py`)

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `map_dim` | `grid_resolution` | attr / ctor param | **High** (205 refs) | Flagship. Reads as *dimensionality*; means *samples per axis* (the cross-section is `grid_resolution × grid_resolution`). |
| `MINIMUM_MAP_DIMENSION` | `MINIMUM_GRID_RESOLUTION` | constant | Low (7) | Track the rename above. |
| `get_maps` | `get_coordinate_grids` | method | **High** (57) | Returns `np.meshgrid` X/Y[/Z] arrays — *coordinate grids*, not "maps"; `maps` also evokes the `map` builtin. |
| `maps` | `coordinate_grids` | attr (cache) | Low (7) | Mirror the getter. |
| `get_mask` | `get_outer_diameter_mask` | method | Med (35) | Boolean, `True` for cells *beyond the outer-diameter circle* (the casing wall). Ties the name to the `outer_diameter` attribute that defines it. |
| `mask` | `outer_diameter_mask` | attr (cache) | Low (7) | Mirror the getter. |
| `get_cell_size` | `get_normalized_spacing` | method | Low (12) | Returns `1/grid_points` — a *normalized* (dimensionless) spacing, not metres. |
| `get_normalized_length` | `get_axial_resolution` | method | Med (18) | Returns an **int count** of z-axis samples (the axial sibling of `grid_resolution`), not a length and not a coordinate. |
| `_validate_normalized_length` | `_validate_axial_resolution` | method (priv) | Low | Track the rename above. |

### 2 · Unit / coordinate conversion (`base.py`, `stl.py`, `_3d.py`)

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `map_to_length` | `cells_to_meters` | method | Med (46, 1 ext test) | Encode the transform: cell count → metres (`× outer_diameter / grid_points`). *Deviation from the raw research's `pixels_to_meters`: this base method serves both 2D pixels and 3D voxels, so the dimension-neutral "cells" is preferred; US spelling matches `outer_diameter`.* |
| `map_to_area` | `cells_to_square_meters` | method | Low (17) | Cell-area count → m² (`× outer_diameter² / grid_points²`). |
| `get_voxel_size` | `get_grid_spacing` | method (stl) | Low (11) | The trimesh voxelization `pitch`; *grid spacing* is the canonical scikit-image/SimpleITK term and avoids implying a volume. |
| `get_volume_per_element` | `get_voxel_volume` | method (`_3d`) | Low (7) | "Element" is vague (FEM node? cell?); it is the volume of one cubic voxel. |

### 3 · Face maps & inhibition (`base.py`, `_2d.py`, `_3d.py`)

The masking story is clarified by splitting two concepts that currently share
the name `outside`/`invalid`: the **pure casing** mask (`outer_diameter_mask`,
§1) vs. the **full exclusion** mask that also carries inhibited surfaces (the
array actually handed to `np.ma.MaskedArray`), named `excluded_mask`. *This
reconciles two overlapping research proposals into one coherent scheme.*

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `_apply_inhibition` | `_apply_surface_inhibition` | method | Low | Keep `_` (it is `super()`-chained, not public). Verb + object. (No `_mask` suffix: it mutates both `face_map` and the mask.) |
| `outside` (param & local in `get_masked_face`) | `excluded_mask` | param / local | Low | Cells excluded from the burn domain = casing exterior **plus** inhibited surfaces. |
| `invalid` (in `get_face_map`) | `excluded_mask` | local | Low | Same set, from the regression map's mask. |
| `boundary_ring` | `outer_surface_boundary` | local | Low | The thin ring of outer-surface cells inhibition is applied to. |
| `bore_mask` (`_2d`) | `inner_surface_inhibited_cells` | local | Low | Bore cells inhibited when the inner surface is restricted. |
| `end_face_zeros` (`_3d`) | `end_face_inhibited_cells` | local | Low | End-face burning cells masked when an end is inhibited (`zeros` was "zeros of what?"). |
| `maskarr` (in `get_face_map`) | `occupancy_state` | local | Low | The thresholded 1/0/-1 indicator array; spell out the abbreviation. |

### 4 · Regression distance field (`base.py`, `_3d.py`)

Unify the grid-spacing vocabulary: `pitch`, `spacing`, and `voxel_spacing` all
become **`*_grid_spacing`** (the scikit-image `spacing=` convention).

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `_regression_distance` | `_compute_regression_distance` | method (priv) | Low | Active verb; keeps the `regression` vocabulary and the `_`. |
| `regression_field` (`_3d` locals) | `distance_field` | local | Low | The masked scalar field fed to marching cubes; standard comp-geo term. |
| `axial_pitch`, `axial_spacing` | `axial_grid_spacing` | local | Low | `pitch` is mechanical jargon; `dx` along z. |
| `radial_pitch`, `radial_spacing` | `radial_grid_spacing` | local | Low | `dx` along x/y. |
| `voxel_spacing` | `grid_spacing` | local | Low | The per-axis spacing tuple; consistent with the components above. |
| `axial_web` | `normalized_axial_web_distance` | local | Low | End-burner fill value: a normalized, axial web distance. |
| `exposed_ends` | `exposed_end_count` | local | Low | An integer count (0/1/2), not a collection; qualifier-last. |

### 5 · Contours, level sets & iso-surfaces (`contours.py`, `_2d.py`, `_3d.py`, `base.py`)

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `get_contours` (in `contours.py`) | `get_iso_contours` | function | Low (13) | Extracts level-set (iso) contours via marching squares. |
| `map` (param of above) | `regression_field` | param | Low | Shadows the `map` builtin; it is the scalar regression field. |
| `map_dist` (param of above) | `iso_level` | param | Low | The threshold level for level-set extraction (scikit-image `level=`). |
| `map_size` (param of `get_length`) | `grid_resolution` | param | Low | All call sites pass `map_dim`; same concept as §1. |
| `offset` (in `get_length`) | `shifted_vertices` | local | Low | `np.roll`-ed copy used to form consecutive-vertex segments. |
| `lengths` | `segment_lengths` | local | Low | Per-segment magnitudes, not a total. |
| `center_offset` | `center_position` | local | Low | An absolute centre coordinate, not a displacement. |
| `radius` | `distance_from_center` | local | Low | Per-vertex distances, not a fixed circle radius. |
| `valid` | `is_interior_contour_segment` | local | Low | Boolean predicate selecting interior (non-wall) segments. |
| `_measure_iso_surface_area` (`_3d`) | `_compute_iso_surface_area` | method (priv) | Low | Active verb; keep `_`. |
| `regression_slice` (`_3d`) | `axial_slice` | local | Low | A 2D cross-section at one axial index. |
| `z_index` (`_3d`) | `axial_index` | local | Low | The axial slice index. |
| `length_normalized` (param of `_3d.get_contours`) | `axial_position_normalized` | param | Med | It is a normalized axial position, not a length. |
| `levels` (`_3d`) | `iso_levels` | local | Low | Level-set thresholds swept by marching cubes. |
| `surface_areas` (`_3d`) | `iso_surface_areas` | local | Low | Areas of the iso-surfaces at each level. |
| `sample_count` (`_3d`) | `iso_level_count` | local | Low | Count of iso-levels sampled (aligned with `_2d` below). |
| `map_distance` (`_2d`) | `web_distance_normalized` | local | Low | Matches the existing name in `base.py`. |

`contours.get_length` itself is **kept** — a 2-call-site helper whose docstring
already explains the interior-segment filtering; `measure_interior_contour_length`
adds length without proportional clarity.

### 6 · Ballistic-property interpolators (`_2d.py`, `_3d.py`)

Drop the `interp_func` coinage for SciPy's term **interpolator**; tag every
per-level series and coordinate frame.

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `get_face_area_interp_func` | `get_face_area_interpolator` | method | Low (14) | `scipy.interpolate` returns an *interpolator*. |
| `face_area_interp_func` | `face_area_interpolator` | attr | Low | Mirror the getter. |
| `get_burn_area_interp_func` | `get_burn_area_interpolator` | method | Low (30) | Same. |
| `burn_area_interp_func` | `burn_area_interpolator` | attr | Low | Mirror the getter. |
| `n_le` | `count_at_or_below_level` | local | Low | `searchsorted` count ≤ each iso-level; spell out `n`/`le`. |
| `counts` | `solid_cell_count` | local | Low | Complement: still-solid cells per level. |
| `step_count` | `iso_level_count` | local | Low | Number of iso-levels (aligned with `_3d`). |
| `distances` | `iso_levels_normalized` | local | Low | Normalized thresholds = interpolator x-data. |
| `values` | `regression_distances_sorted` | local | Low | Sorted field values = interpolator y-source. |
| `max_dist` | `max_regression_distance` | local | Low | Disambiguate "max distance in which space?". |
| `max_level` (`_3d`) | `max_iso_level` | local | Low | Largest regression value sampled. |
| `face_area_values` | `face_area_per_iso_level` | local | Low | Array indexed by iso-level. |
| `perimeter_values` | `core_perimeter_per_iso_level` | local | Low | Core perimeter per level. |
| `core_area_values` | `core_area_per_iso_level` | local | Low | Core (bore) area per level. |
| `total_face_area_values` | `exposed_end_area_per_iso_level` | local | Low | End-face contribution per level. |
| `burn_area_values` | `burn_area_per_iso_level` | local | Low | Core + ends, pre-smoothing. |
| `length_values` | `grain_length_per_web` | local | Low | Axial length after end regression, per web. |
| `web_distances` | `web_distances_denormalized` | local | Low | Denormalized values in metres (`_denormalized` frame). |
| `smoothed_face_area` | `face_area_smoothed` | local | Low | Qualifier-last. |
| `smoothed_burn_area`, `smoothed_areas` (`_3d`) | `burn_area_smoothed` | local | Low | Qualifier-last; unifies 2D & 3D. |

### 7 · Mass-property helpers & STL (`_2d.py`, `_3d.py`, `stl.py`)

| Current | → Proposed | Kind | Risk | Why |
|---|---|---|---|---|
| `_get_active_material_indices` | `_find_solid_material_indices` | method (priv) | Low | `find` for a search; "solid" (face==1), not vague "active". Keep `_`. |
| `_indices_to_normalized_coords` | `_indices_to_grid_coordinates` | method (priv) | Low | Names the target frame (normalized grid). Keep `_`. |
| `center_shift` | `grid_center_index` | local | Low | `grid_points / 2` — the origin's index, not a "shift". |
| `x_coords/y_coords/z_coords` | `x_grid/y_grid/z_grid` | local | Low | Normalized grid frame (`_grid`); distinct from the `_denormalized` arrays they feed. |
| `moi` | `inertia_tensor` | local | Low | 3×3 tensor, not a scalar moment; un-abbreviate. |
| `I_axial` (`_2d`) | `axial_inertia_contribution` | local | Low | The `M·L²/12` term added to the radial axes. |
| `n_elements` (`_2d`) | `solid_element_count` | local | Low | Avoid `n_`; qualifier-last. |
| `active_elements` (`_3d`) | `solid_voxel_count` | local | Low | "solid" not "active"; `voxel` for 3D. |
| `lower_recession` / `upper_recession` (`_2d`) | `lower_end_recession` / `upper_end_recession` | local | Low | Keep the SRM term "recession"; add "end". |
| `axial_cog` (`_2d`) | `axial_center_of_gravity_position` | local | Low | A spatial coordinate; abbreviation spelled out. |

---

## Rollout

Sequenced so the bulk of the readability win lands with near-zero risk first,
and the wide-blast renames land last as isolated, atomic commits. Each step is
its own branch/PR per the project's one-concern-per-PR convention.

- **Step 1 — Local variables (Low risk, no external impact).** Categories
  §3 locals, §4 locals, §5 locals, §6 locals, §7 locals. Confined to function
  bodies; nothing outside the module sees them. Biggest clarity-per-line gain.
- **Step 2 — Private methods (Low).** `_apply_surface_inhibition`,
  `_compute_regression_distance`, `_compute_iso_surface_area`,
  `_find_solid_material_indices`, `_indices_to_grid_coordinates`,
  `_validate_axial_grid_points`, plus `contours.get_iso_contours` and its params.
  Contained to `fmm/`.
- **Step 3 — Cached attributes + their getters (Low–Med).** `coordinate_grids`,
  `exterior_mask`, the `*_interpolator` pairs, `get_normalized_spacing`,
  `get_grid_spacing`, `get_voxel_volume`. Update intra-module call sites.
- **Step 4 — Wide-blast public-of-module names (High), one PR each.**
  `map_dim → grid_resolution` (+ `MINIMUM_GRID_RESOLUTION`), `get_maps →
  get_coordinate_grids`, `get_mask → get_outer_diameter_mask`,
  `get_normalized_length → get_axial_resolution`, `cells_to_meters` /
  `cells_to_square_meters`. Each must update the geometry subclasses, tests,
  and the docs (below) in the same commit.

**Docs move with the code.** Every step that renames a name appearing in prose
must update it in the same PR: this module's [`README.md`](README.md) (which
walks through `generate_initial_face_map`, `get_outer_diameter_mask`,
`get_regression_map`, `get_face_map`, `get_contours`,
`get_face_area_interpolator`, `get_burn_area_interpolator`, …), the
`docs/explanations/grain_regression.md` walkthrough
and call-flow diagrams, the `docs/api/models/grain/` reference pages, and the
generated `site/`. After a docs-affecting rename, rebuild the site so the
generated HTML matches.

Mechanical safety net: these are pure renames, so `git grep` + the test suite
(`tests/test_models/test_propulsion/test_grain/`, which exercises 2D/3D burn
area, CoG, MoI, inhibition) gives a hard pass/fail per step. Watch the one
external test reference for `map_to_length`
(`tests/.../test_grainsegment3d/test_finocyl_solidworks.py`).
