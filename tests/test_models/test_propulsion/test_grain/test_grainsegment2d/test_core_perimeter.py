"""The traced core perimeter holds up against an analytic front near the casing.

A rod and tube grain burns as two concentric circles, so its core perimeter is
known in closed form at every web distance. The traced perimeter has to match
it at any grid resolution, including once the front has regressed to within a
cell or two of the casing.
"""

import numpy as np
import pytest

import machwave.models.grain as grain_models
import machwave.models.grain.fmm.contours as fmm_contours
from tests.factories import RodAndTubeGrainSegmentFactory

LENGTH = 0.2
OUTER_DIAMETER = 0.1
ROD_OUTER_DIAMETER = 0.01
TUBE_INNER_DIAMETER = 0.03
PERIMETER_TOLERANCE = 0.02


def _analytic_core_perimeter(web_distance, outer_surface_inhibited=True):
    """Rod outer surface, tube inner surface and, if exposed, tube outer surface."""
    rod_radius = ROD_OUTER_DIAMETER / 2 - web_distance
    tube_radius = TUBE_INNER_DIAMETER / 2 + web_distance

    perimeter = 0.0
    if rod_radius > 0:
        perimeter += 2 * np.pi * rod_radius
    if tube_radius < OUTER_DIAMETER / 2:
        perimeter += 2 * np.pi * tube_radius
    if not outer_surface_inhibited:
        perimeter += 2 * np.pi * (OUTER_DIAMETER / 2 - web_distance)
    return perimeter


def _build_segment_with_exposed_outer_surface(grid_resolution):
    return RodAndTubeGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        rod_outer_diameter=ROD_OUTER_DIAMETER,
        tube_inner_diameter=TUBE_INNER_DIAMETER,
        grid_resolution=grid_resolution,
        inhibited_surfaces=grain_models.InhibitedSurfaces(outer_surface=False),
    )


@pytest.mark.parametrize("grid_resolution", [100, 101, 200, 201])
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


@pytest.mark.parametrize("grid_resolution", [100, 200])
def test_exposed_outer_surface_traces_the_front_and_not_the_casing(grid_resolution):
    segment = _build_segment_with_exposed_outer_surface(grid_resolution)

    web_distance = 0.5 * segment.get_web_thickness()

    assert segment.get_core_perimeter(web_distance) == pytest.approx(
        _analytic_core_perimeter(web_distance, outer_surface_inhibited=False),
        rel=PERIMETER_TOLERANCE,
    )


@pytest.mark.parametrize("grid_resolution", [100, 200])
def test_exposed_outer_surface_burn_area_matches_the_analytic_front(grid_resolution):
    segment = _build_segment_with_exposed_outer_surface(grid_resolution)

    web_distance = 0.5 * segment.get_web_thickness()
    outer_radius = OUTER_DIAMETER / 2 - web_distance
    tube_radius = TUBE_INNER_DIAMETER / 2 + web_distance
    rod_radius = max(ROD_OUTER_DIAMETER / 2 - web_distance, 0.0)
    face_area = np.pi * (outer_radius**2 - tube_radius**2 + rod_radius**2)
    burn_area = (
        _analytic_core_perimeter(web_distance, outer_surface_inhibited=False)
        * (LENGTH - 2 * web_distance)
        + 2 * face_area
    )

    assert segment.get_burn_area(web_distance) == pytest.approx(
        burn_area, rel=PERIMETER_TOLERANCE
    )


@pytest.mark.parametrize("grid_resolution", [200, 201])
def test_inhibited_casing_leaves_no_perimeter_once_the_bore_reaches_it(
    grid_resolution,
):
    segment = RodAndTubeGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        rod_outer_diameter=ROD_OUTER_DIAMETER,
        tube_inner_diameter=TUBE_INNER_DIAMETER,
        grid_resolution=grid_resolution,
    )

    web_distance = 1.2 * segment.get_web_thickness()

    assert segment.get_core_perimeter(web_distance) == 0.0
    assert segment.get_contours(web_distance) == []


def test_contour_length_includes_the_closing_segment_of_a_closed_contour():
    square = np.array([[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0], [0.0, 0.0]])

    assert fmm_contours.get_length(square) == pytest.approx(8.0)


def test_contour_length_does_not_close_an_open_contour():
    open_square = np.array([[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]])

    assert fmm_contours.get_length(open_square) == pytest.approx(6.0)
