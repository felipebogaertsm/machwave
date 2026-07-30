"""Mass property coordinates are read at the spacing of the grid they sit on.

Cell indices become positions through the axial and radial grid spacings, which
differ from each other. Converting either axis at the wrong spacing drags the
center of gravity off the segment midpoint and skews the inertia tensor.
"""

import numpy as np
import pytest

from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
IDEAL_DENSITY = 1750.0
INERTIA_TOLERANCE = 0.01


def _constant_bore_segment(length):
    return ConicalGrainSegmentFactory.build(
        length=length,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
    )


@pytest.mark.parametrize("length", [0.3, 0.02])
def test_axial_center_of_gravity_is_the_segment_midpoint(length):
    segment = _constant_bore_segment(length)

    center_of_gravity = segment.get_center_of_gravity(web_distance=0.0)

    assert center_of_gravity[0] == pytest.approx(length / 2, rel=1e-3)


@pytest.mark.parametrize("length", [0.3, 0.02])
def test_moment_of_inertia_matches_the_hollow_cylinder(length):
    """A constant-bore conical is a hollow cylinder, whose inertia is exact.

    Both terms are taken against the segment's own mass, so the check is on the
    coordinates alone and not on how the voxel count reads the mass.
    """
    segment = _constant_bore_segment(length)

    outer_radius = OUTER_DIAMETER / 2
    core_radius = CORE_DIAMETER / 2
    mass = segment.get_mass(0.0, IDEAL_DENSITY)
    radius_term = mass * (outer_radius**2 + core_radius**2)
    expected_axial = 0.5 * radius_term
    expected_transverse = 0.25 * radius_term + mass * length**2 / 12

    inertia = segment.get_moment_of_inertia(IDEAL_DENSITY, 0.0)

    assert inertia[0, 0] == pytest.approx(expected_axial, rel=INERTIA_TOLERANCE)
    assert inertia[1, 1] == pytest.approx(expected_transverse, rel=INERTIA_TOLERANCE)
    assert inertia[2, 2] == pytest.approx(expected_transverse, rel=INERTIA_TOLERANCE)


def test_transverse_inertia_axes_match_for_a_concentric_segment():
    segment = _constant_bore_segment(0.3)

    inertia = segment.get_moment_of_inertia(IDEAL_DENSITY, 0.0)

    assert inertia[1, 1] == pytest.approx(inertia[2, 2])
    assert np.allclose(inertia - np.diag(np.diag(inertia)), 0.0, atol=1e-9)
