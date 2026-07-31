"""Axial positions map onto slice indices the same way everywhere in 3D FMM.

An axial position is a fraction of the segment length measured from the aft
end, so it has to be scaled by the axial resolution and clamped to the grid
before it indexes a slice.
"""

import numpy as np
import pytest

from tests.factories import ConicalGrainSegmentFactory

LENGTH = 68e-3
OUTER_DIAMETER = 41e-3
LOWER_CORE_DIAMETER = 30e-3  # aft (nozzle) end
UPPER_CORE_DIAMETER = 8e-3  # forward (bulkhead) end
BORE_TOLERANCE_IN_CELLS = 3.0


@pytest.fixture(scope="module")
def tapered_segment():
    return ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=UPPER_CORE_DIAMETER,
        lower_core_diameter=LOWER_CORE_DIAMETER,
    )


def _bore_width_in_cells(segment, axial_position_normalized):
    """Width of the single traced bore contour, in cells."""
    (contour,) = segment.get_contours(0.0, axial_position_normalized)
    return float(np.ptp(contour[:, 0]))


def test_axial_index_spans_the_grid(tapered_segment):
    axial_resolution = tapered_segment.get_axial_resolution()

    assert tapered_segment.get_axial_index(0.0) == 0
    assert tapered_segment.get_axial_index(1.0) == axial_resolution - 1
    assert tapered_segment.get_axial_index(0.5) == axial_resolution // 2


def test_axial_index_clamps_positions_outside_the_segment(tapered_segment):
    last_index = tapered_segment.get_axial_resolution() - 1

    assert tapered_segment.get_axial_index(-2.0) == 0
    assert tapered_segment.get_axial_index(3.0) == last_index


def _assert_same_contours(actual, expected):
    assert len(actual) == len(expected)
    for actual_contour, expected_contour in zip(actual, expected):
        np.testing.assert_allclose(actual_contour, expected_contour)


def test_contours_outside_the_segment_are_clamped_to_the_ends(tapered_segment):
    _assert_same_contours(
        tapered_segment.get_contours(0.0, -2.0), tapered_segment.get_contours(0.0, 0.0)
    )
    _assert_same_contours(
        tapered_segment.get_contours(0.0, 3.0), tapered_segment.get_contours(0.0, 1.0)
    )


@pytest.mark.parametrize("axial_position_normalized", [0.05, 0.5, 0.95])
def test_contours_follow_the_bore_taper(tapered_segment, axial_position_normalized):
    bore_diameter = LOWER_CORE_DIAMETER + axial_position_normalized * (
        UPPER_CORE_DIAMETER - LOWER_CORE_DIAMETER
    )
    expected_width = bore_diameter / OUTER_DIAMETER * tapered_segment.grid_resolution

    assert _bore_width_in_cells(
        tapered_segment, axial_position_normalized
    ) == pytest.approx(expected_width, abs=BORE_TOLERANCE_IN_CELLS)
