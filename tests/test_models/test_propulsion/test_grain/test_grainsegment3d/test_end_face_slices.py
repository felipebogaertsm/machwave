"""An end face burns without eating the slice of propellant behind it.

The burning surface is the boundary between propellant and void, so an end
face is exposed by placing void beyond the segment rather than by emptying its
end slice. Emptying it made the same grain hold less propellant purely because
its ends were allowed to burn.
"""

import numpy as np
import pytest

from machwave.models.grain.base import InhibitedSurfaces
from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
VOLUME_TOLERANCE = 0.02

BOTH_ENDS_INHIBITED = InhibitedSurfaces(
    outer_surface=True, upper_end=True, lower_end=True
)


def _constant_bore_segment(length, inhibited_surfaces=None):
    return ConicalGrainSegmentFactory.build(
        length=length,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
        inhibited_surfaces=inhibited_surfaces,
    )


@pytest.mark.parametrize("length", [0.3, 0.02])
def test_exposed_ends_hold_the_same_propellant_as_inhibited_ends(length):
    exposed = _constant_bore_segment(length)
    inhibited = _constant_bore_segment(length, BOTH_ENDS_INHIBITED)

    assert exposed.get_volume(0.0) == pytest.approx(inhibited.get_volume(0.0))


@pytest.mark.parametrize("length", [0.3, 0.02])
def test_volume_matches_the_analytic_hollow_cylinder(length):
    """Short segments used to lose a tenth of their propellant to the end slices."""
    segment = _constant_bore_segment(length)

    expected = np.pi / 4 * (OUTER_DIAMETER**2 - CORE_DIAMETER**2) * length

    assert segment.get_volume(0.0) == pytest.approx(expected, rel=VOLUME_TOLERANCE)


def test_axial_slices_tile_the_segment_length():
    segment = _constant_bore_segment(0.3)

    axial_extent = segment.get_axial_resolution() * segment.get_axial_grid_spacing()

    assert axial_extent == pytest.approx(segment.length)


def test_exposed_end_face_burns_from_the_end_of_the_segment():
    """The end slice is one axial step from the front, not already consumed."""
    segment = _constant_bore_segment(0.3)

    end_slice_depth = float(segment.get_regression_map()[0].max())
    axial_step = segment.normalize(segment.get_axial_grid_spacing())

    assert end_slice_depth == pytest.approx(axial_step, rel=0.01)


def test_inhibited_end_face_does_not_burn():
    segment = _constant_bore_segment(0.3, BOTH_ENDS_INHIBITED)

    end_slice_depth = float(segment.get_regression_map()[0].max())
    axial_step = segment.normalize(segment.get_axial_grid_spacing())

    assert end_slice_depth > 10 * axial_step
