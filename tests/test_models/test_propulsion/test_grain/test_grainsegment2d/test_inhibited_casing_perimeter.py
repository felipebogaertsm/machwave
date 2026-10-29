"""An inhibited casing in contact with the port does not count as burning perimeter.

A D-grain port is bounded by the slot face and the casing. With the casing
inhibited, only the slot face burns, so the core perimeter is the chord
`2 * sqrt(R^2 - (c - w)^2)` at every web distance.
"""

import math

import pytest

import machwave.models.grain.geometries as grain_geometries

OUTER_RADIUS = 0.05
SLOT_OFFSET = 0.01
LENGTH = 0.2
TOLERANCE = 0.02


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
