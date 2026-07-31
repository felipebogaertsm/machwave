"""Cells convert to metres at the spacing of the grid they were sampled on.

The cross-section grid spans the outer diameter over `grid_resolution`
samples, so it holds `grid_resolution - 1` intervals. Dividing by the sample
count instead shrinks every length and area read off the grid, and since the
port area is the casing area less the face area, the whole deficit lands on
the port.
"""

import numpy as np
import pytest

from tests.factories import ConicalGrainSegmentFactory, RodAndTubeGrainSegmentFactory

OUTER_DIAMETER = 0.1
ROD_OUTER_DIAMETER = 0.01
TUBE_INNER_DIAMETER = 0.03
PORT_AREA_TOLERANCE = 0.05


@pytest.mark.parametrize("grid_resolution", [100, 200])
def test_cells_span_the_outer_diameter(grid_resolution):
    segment = RodAndTubeGrainSegmentFactory.build(
        length=0.2, outer_diameter=OUTER_DIAMETER, grid_resolution=grid_resolution
    )
    interval_count = grid_resolution - 1

    assert segment.cells_to_meters(interval_count) == pytest.approx(OUTER_DIAMETER)
    assert segment.cells_to_square_meters(interval_count**2) == pytest.approx(
        OUTER_DIAMETER**2
    )


@pytest.mark.parametrize("grid_resolution", [100, 200])
def test_2d_port_area_matches_the_analytic_annulus(grid_resolution):
    segment = RodAndTubeGrainSegmentFactory.build(
        length=0.2,
        outer_diameter=OUTER_DIAMETER,
        rod_outer_diameter=ROD_OUTER_DIAMETER,
        tube_inner_diameter=TUBE_INNER_DIAMETER,
        grid_resolution=grid_resolution,
    )

    expected = np.pi / 4 * (TUBE_INNER_DIAMETER**2 - ROD_OUTER_DIAMETER**2)

    assert segment.get_port_area(0.0) == pytest.approx(
        expected, rel=PORT_AREA_TOLERANCE
    )


@pytest.mark.parametrize("grid_resolution", [100, 200])
def test_3d_port_area_matches_the_analytic_bore(grid_resolution):
    core_diameter = 0.03
    segment = ConicalGrainSegmentFactory.build(
        length=0.2,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=core_diameter,
        lower_core_diameter=core_diameter,
        grid_resolution=grid_resolution,
    )

    expected = np.pi / 4 * core_diameter**2

    assert segment.get_port_area(0.0, 0.1) == pytest.approx(
        expected, rel=PORT_AREA_TOLERANCE
    )


def test_web_thickness_matches_the_analytic_web():
    """The tube burns from its bore out to the casing."""
    segment = RodAndTubeGrainSegmentFactory.build(
        length=0.2,
        outer_diameter=OUTER_DIAMETER,
        rod_outer_diameter=ROD_OUTER_DIAMETER,
        tube_inner_diameter=TUBE_INNER_DIAMETER,
    )

    expected = (OUTER_DIAMETER - TUBE_INNER_DIAMETER) / 2

    assert segment.get_web_thickness() == pytest.approx(expected, rel=0.01)
