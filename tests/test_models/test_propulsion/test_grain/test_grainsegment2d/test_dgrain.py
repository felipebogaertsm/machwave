import math

import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.geometries as grain_geometries

OUTER_RADIUS = 0.05
SLOT_OFFSET = 0.01
LENGTH = 0.2
TOLERANCE = 0.02


def test_dgrain_segment_geometry_validation():
    # Control group:
    _ = grain_geometries.DGrainSegment(
        outer_diameter=100e-3,
        slot_offset=30e-3,
        length=120e-3,
    )

    # Negative slot offset:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=-30e-3,
            length=120e-3,
        )

    # Slot offset larget than segment radius:
    with pytest.raises(grain_models.GrainGeometryError):
        _ = grain_geometries.DGrainSegment(
            outer_diameter=100e-3,
            slot_offset=55e-3,
            length=120e-3,
        )


def _chord(web_distance):
    return 2 * math.sqrt(OUTER_RADIUS**2 - (SLOT_OFFSET - web_distance) ** 2)


def _build_dgrain(grid_resolution):
    return grain_geometries.DGrainSegment(
        length=LENGTH,
        outer_diameter=2 * OUTER_RADIUS,
        slot_offset=SLOT_OFFSET,
        grid_resolution=grid_resolution,
    )


@pytest.mark.parametrize("grid_resolution", [200, 201])
@pytest.mark.parametrize("web_distance", [0.0, 0.01, 0.03])
def test_dgrain_core_perimeter_is_the_slot_chord(grid_resolution, web_distance):
    segment = _build_dgrain(grid_resolution)

    assert segment.get_core_perimeter(web_distance) == pytest.approx(
        _chord(web_distance), rel=TOLERANCE
    )


@pytest.mark.parametrize("grid_resolution", [200, 201])
def test_dgrain_burn_area_excludes_the_casing(grid_resolution):
    segment = _build_dgrain(grid_resolution)
    web_distance = 0.03
    burn_area = _chord(web_distance) * (
        LENGTH - 2 * web_distance
    ) + 2 * segment.get_face_area(web_distance)

    assert segment.get_burn_area(web_distance) == pytest.approx(
        burn_area, rel=TOLERANCE
    )
