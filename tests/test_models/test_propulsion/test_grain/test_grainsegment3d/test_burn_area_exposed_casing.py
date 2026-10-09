import numpy as np
import pytest

from machwave.models.grain.base import InhibitedSurfaces
from tests.factories import ConicalGrainSegmentFactory

OUTER_DIAMETER = 0.1
CORE_DIAMETER = 0.03
LENGTH = 0.1


def _hollow_cylinder(inhibited_surfaces):
    return ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=CORE_DIAMETER,
        lower_core_diameter=CORE_DIAMETER,
        inhibited_surfaces=inhibited_surfaces,
    )


@pytest.mark.parametrize("fraction", [0.5, 0.9])
def test_burn_area_with_exposed_ends_matches_hollow_cylinder(fraction):
    segment = _hollow_cylinder(InhibitedSurfaces())
    web = fraction * segment.get_web_thickness()
    port_diameter = CORE_DIAMETER + 2 * web
    expected = np.pi * port_diameter * (LENGTH - 2 * web) + 2 * np.pi / 4 * (
        OUTER_DIAMETER**2 - port_diameter**2
    )
    assert segment.get_burn_area(web) == pytest.approx(expected, rel=0.03)


@pytest.mark.parametrize(
    "inhibited_surfaces",
    [
        pytest.param(
            InhibitedSurfaces(outer_surface=True, upper_end=True, lower_end=False),
            id="aft-end-exposed",
        ),
        pytest.param(
            InhibitedSurfaces(outer_surface=False, upper_end=True, lower_end=True),
            id="outer-surface-exposed",
        ),
    ],
)
def test_burn_area_integral_matches_swept_volume(inhibited_surfaces):
    segment = _hollow_cylinder(inhibited_surfaces)
    web_thickness = segment.get_web_thickness()
    webs = np.linspace(0.0, web_thickness, 300)
    integral = np.trapezoid([segment.get_burn_area(w) for w in webs], webs)
    assert integral / segment.get_volume(0.0) == pytest.approx(1.0, abs=0.03)
