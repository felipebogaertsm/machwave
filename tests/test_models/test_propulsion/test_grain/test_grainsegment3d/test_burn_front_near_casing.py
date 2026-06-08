"""A burning front that regresses near the casing must still be counted.

A fixed edge exclusion once dropped the front over the last few pixels of web,
collapsing the burn area near burnout. These check a pure-radial tube (inhibited
ends, inhibited outer wall) whose analytical lateral area pi * (core + 2w) * L is
known at every web, including close to the casing.
"""

import numpy as np
import pytest

from machwave.models.grain.base import InhibitedSurfaces
from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
LENGTH = 0.1
INHIBITED_ENDS = InhibitedSurfaces(outer_surface=True, upper_end=True, lower_end=True)


@pytest.fixture
def radial_tube():
    segment = ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
        inhibited_surfaces=INHIBITED_ENDS,
    )
    segment.map_dim = 150
    return segment


def _analytical_lateral_area(web):
    return np.pi * (CORE_DIAMETER + 2 * web) * LENGTH


def test_burn_area_holds_near_the_casing(radial_tube):
    web_thickness = radial_tube.get_web_thickness()
    for fraction in (0.90, 0.95):
        web = web_thickness * fraction
        ratio = radial_tube.get_burn_area(web) / _analytical_lateral_area(web)
        assert ratio == pytest.approx(1.0, abs=0.1)


def test_impulse_integral_matches_swept_volume(radial_tube):
    web_thickness = radial_tube.get_web_thickness()
    webs = np.linspace(0.0, web_thickness, 300)
    integral = np.trapezoid([radial_tube.get_burn_area(w) for w in webs], webs)
    volume = LENGTH * np.pi * (OUTER_DIAMETER**2 - CORE_DIAMETER**2) / 4
    assert integral / volume == pytest.approx(1.0, abs=0.05)
