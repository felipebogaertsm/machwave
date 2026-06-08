"""Burn area must not scale with the length-to-outer-diameter ratio.

A pure-radial tube (inhibited ends, constant bore) has the exact lateral burn
area pi * core_diameter * length at ignition, independent of how long the tube
is. The 3D FMM once scaled this by length / outer_diameter; these guard that the
ignition burn area stays near the analytical value and, above all, stays
constant across length-to-outer-diameter ratios.
"""

import numpy as np
import pytest

from machwave.models.grain.base import InhibitedSurfaces
from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
INHIBITED_ENDS = InhibitedSurfaces(outer_surface=True, upper_end=True, lower_end=True)
LENGTH_TO_DIAMETER_RATIOS = [0.5, 1.0, 2.0, 3.0]


def _radial_tube(length_to_diameter):
    return ConicalGrainSegmentFactory.build(
        length=length_to_diameter * OUTER_DIAMETER,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
        inhibited_surfaces=INHIBITED_ENDS,
    )


@pytest.mark.parametrize("length_to_diameter", LENGTH_TO_DIAMETER_RATIOS)
def test_ignition_burn_area_matches_radial_tube(length_to_diameter):
    segment = _radial_tube(length_to_diameter)
    expected = np.pi * CORE_DIAMETER * (length_to_diameter * OUTER_DIAMETER)
    assert segment.get_burn_area(0.0) == pytest.approx(expected, rel=0.07)


def test_burn_area_is_constant_across_length_to_diameter():
    ratios = [
        _radial_tube(r).get_burn_area(0.0)
        / (np.pi * CORE_DIAMETER * (r * OUTER_DIAMETER))
        for r in LENGTH_TO_DIAMETER_RATIOS
    ]
    assert max(ratios) / min(ratios) < 1.03
