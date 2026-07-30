"""Concentric grains put their center of gravity on the motor axis.

The cell grid spans -1 to 1 over grid_resolution samples, so its center index
is (grid_resolution - 1) / 2. Taking it as grid_resolution / 2 offsets every
cell by half a cell and drags the transverse center of gravity off the axis.
"""

import pytest

from tests.factories import ConicalGrainSegmentFactory, RodAndTubeGrainSegmentFactory

OUTER_DIAMETER = 0.1
LENGTH = 0.2
OFF_AXIS_TOLERANCE_IN_CELLS = 0.01


def test_2d_concentric_segment_center_of_gravity_is_on_the_axis():
    segment = RodAndTubeGrainSegmentFactory.build(
        length=LENGTH, outer_diameter=OUTER_DIAMETER
    )

    center_of_gravity = segment.get_center_of_gravity(web_distance=0.0)
    tolerance = segment.cells_to_meters(OFF_AXIS_TOLERANCE_IN_CELLS)

    assert center_of_gravity[1] == pytest.approx(0.0, abs=tolerance)
    assert center_of_gravity[2] == pytest.approx(0.0, abs=tolerance)


def test_3d_concentric_segment_center_of_gravity_is_on_the_axis():
    segment = ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=0.03,
        lower_core_diameter=0.03,
    )

    center_of_gravity = segment.get_center_of_gravity(web_distance=0.0)
    tolerance = segment.cells_to_meters(OFF_AXIS_TOLERANCE_IN_CELLS)

    assert center_of_gravity[1] == pytest.approx(0.0, abs=tolerance)
    assert center_of_gravity[2] == pytest.approx(0.0, abs=tolerance)
