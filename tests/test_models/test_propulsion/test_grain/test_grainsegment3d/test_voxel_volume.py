"""The 3D FMM grid is anisotropic, so its cell volume is not a cube.

The axial spacing follows the axial resolution and the radial spacing follows
the grid resolution; taking the cell as a radial cube biases every volume and
mass derived from a voxel count.
"""

import numpy as np
import pytest

from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
VOLUME_TOLERANCE = 0.02


def _constant_bore_segment(length):
    return ConicalGrainSegmentFactory.build(
        length=length,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
    )


def test_voxel_volume_is_the_anisotropic_cell():
    segment = _constant_bore_segment(0.3)

    axial_spacing = segment.get_axial_grid_spacing()
    radial_spacing = segment.get_radial_grid_spacing()

    assert axial_spacing != pytest.approx(radial_spacing)
    assert segment.get_voxel_volume() == pytest.approx(
        radial_spacing**2 * axial_spacing
    )


@pytest.mark.parametrize("length_to_diameter_ratio", [2.0, 3.0])
def test_volume_matches_the_analytic_hollow_cylinder(length_to_diameter_ratio):
    """A constant-bore conical is a hollow cylinder, whose volume is exact."""
    length = length_to_diameter_ratio * OUTER_DIAMETER
    segment = _constant_bore_segment(length)

    expected = np.pi / 4 * (OUTER_DIAMETER**2 - CORE_DIAMETER**2) * length

    assert segment.get_volume(0.0) == pytest.approx(expected, rel=VOLUME_TOLERANCE)
