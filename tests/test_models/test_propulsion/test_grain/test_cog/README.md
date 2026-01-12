# Grain Center of Gravity (CoG) Tests

This directory contains comprehensive tests for grain center of gravity calculations across different grain geometries.

## Test Structure

### BATES Grains

- **File**: `test_bates_cog.py`
- **Geometries**: BATES (cylindrical grains)
- **Tests**: 9 tests covering single/multi-segment configurations

### FMM 2D Grains (Parametrized)

- **File**: `test_fmm2d_cog.py`
- **Geometries**: All geometries inheriting from `FMMGrainSegment2D`
  - StarGrainSegment
  - WagonWheelGrainSegment
  - RodAndTubeGrainSegment
  - MultiPortGrainSegment
  - DGrainSegment
- **Tests**: 8 test functions × 5 geometries = 40 tests
- **Test Classes**:
  - `TestFMM2DSegmentCoG`: Single segment tests (3 tests per geometry)
  - `TestFMM2DGrainMultiSegmentCoG`: Multi-segment tests (5 tests per geometry)

### FMM 3D Grains (Parametrized)

- **File**: `test_fmm3d_cog.py`
- **Geometries**: All geometries inheriting from `FMMGrainSegment3D`
  - ConicalGrainSegment
- **Tests**: 9 test functions × 1 geometry = 9 tests
- **Test Classes**:
  - `TestFMM3DSegmentCoG`: Single segment tests (4 tests per geometry)
  - `TestFMM3DGrainMultiSegmentCoG`: Multi-segment tests (5 tests per geometry)

## Adding New Geometries

When adding a new FMM2D or FMM3D geometry:

1. **Create a factory function** in `conftest.py`:

   ```python
   def create_your_geometry_segment(
       length=1.0,
       outer_diameter=0.1,
       density_ratio=1.0,
   ):
       return YourGeometrySegment(
           length=length,
           outer_diameter=outer_diameter,
           # Add geometry-specific parameters here
           density_ratio=density_ratio,
       )
   ```

2. **Add to parametrize fixture** in `conftest.py`:

   - For FMM2D: Add to `fmm2d_geometries`
   - For FMM3D: Add to `fmm3d_geometries`

3. **Run tests** - your new geometry will automatically be tested by all existing tests!

## Test Coverage

### Single Segment Tests

- CoG at ignition (symmetric grains should be at center)
- CoG stability during burn
- Coordinate system verification (port-origin)
- Burnout behavior (3D only)

### Multi-Segment Tests

- Single segment position verification
- Two segments with spacing
- Two segments with zero spacing
- Three segments with burn progression
- Different densities (heavier segment pulls CoG)

## Coordinate System

All FMM grains use a **port-origin** coordinate system:

- Origin at the PORT (aft end, closest to nozzle)
- Positive x-axis points FORWARD toward the bulkhead
- For symmetric grains, CoG should be near the geometric center

## Total Test Count

- **BATES**: 9 tests
- **FMM 2D**: 40 tests (5 geometries × 8 tests each)
- **FMM 3D**: 9 tests (1 geometry × 9 tests)
- **TOTAL**: 58 tests
