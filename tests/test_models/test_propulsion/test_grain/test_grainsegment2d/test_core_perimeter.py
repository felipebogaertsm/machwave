"""The traced core perimeter holds up against an analytic front near the casing.

A rod and tube grain burns as two concentric circles, so its core perimeter is
known in closed form at every web distance. The traced perimeter has to match
it at any grid resolution, including once the front has regressed to within a
cell or two of the casing.
"""

import numpy as np
import pytest

import machwave.models.grain.fmm.contours as fmm_contours
from tests.factories import RodAndTubeGrainSegmentFactory

LENGTH = 0.2
OUTER_DIAMETER = 0.1
ROD_OUTER_DIAMETER = 0.01
TUBE_INNER_DIAMETER = 0.03
PERIMETER_TOLERANCE = 0.02


def _analytic_core_perimeter(web_distance):
    """Rod outer surface and tube inner surface, while each still exists."""
    rod_radius = ROD_OUTER_DIAMETER / 2 - web_distance
    tube_radius = TUBE_INNER_DIAMETER / 2 + web_distance

    perimeter = 0.0
    if rod_radius > 0:
        perimeter += 2 * np.pi * rod_radius
    if tube_radius < OUTER_DIAMETER / 2:
        perimeter += 2 * np.pi * tube_radius
    return perimeter


@pytest.mark.parametrize("grid_resolution", [100, 200])
@pytest.mark.parametrize("web_fraction", [0.5, 0.9, 0.98])
def test_core_perimeter_matches_the_analytic_front(grid_resolution, web_fraction):
    segment = RodAndTubeGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        rod_outer_diameter=ROD_OUTER_DIAMETER,
        tube_inner_diameter=TUBE_INNER_DIAMETER,
        grid_resolution=grid_resolution,
    )

    web_distance = web_fraction * segment.get_web_thickness()

    assert segment.get_core_perimeter(web_distance) == pytest.approx(
        _analytic_core_perimeter(web_distance), rel=PERIMETER_TOLERANCE
    )


def test_contour_length_is_the_closed_polygon_length():
    square = np.array([[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]])

    assert fmm_contours.get_length(square) == pytest.approx(8.0)
