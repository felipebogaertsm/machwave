"""Burn area and volume share one web thickness cutoff.

Areas are held constant so the cutoff is what drives the results to zero,
rather than the geometry running out on its own.
"""

import numpy as np
import pytest

import machwave.models.grain as grain_models

LENGTH = 200e-3
OUTER_DIAMETER = 100e-3
WEB_THICKNESS = 10e-3
CORE_AREA = 2e-3
FACE_AREA = 1e-3


class _ConstantAreaSegment(grain_models.GrainSegment2D):
    """Segment whose areas do not vary with the web distance."""

    def get_web_thickness(self) -> float:
        return WEB_THICKNESS

    def get_core_area(self, web_distance: float) -> float:
        return CORE_AREA

    def get_face_area(self, web_distance: float) -> float:
        return FACE_AREA

    def get_port_area(self, web_distance: float) -> float:
        return FACE_AREA

    def get_center_of_gravity(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        return np.zeros(3, dtype=np.float64)

    def get_moment_of_inertia(self, *args, **kwargs) -> np.typing.NDArray[np.float64]:
        return np.zeros((3, 3), dtype=np.float64)


@pytest.fixture
def segment():
    return _ConstantAreaSegment(length=LENGTH, outer_diameter=OUTER_DIAMETER)


def test_burn_area_and_volume_are_nonzero_at_the_web_thickness(segment):
    assert segment.get_burn_area(WEB_THICKNESS) > 0.0
    assert segment.get_volume(WEB_THICKNESS) > 0.0


def test_burn_area_and_volume_are_zero_past_the_web_thickness(segment):
    for web_distance in (np.nextafter(WEB_THICKNESS, np.inf), WEB_THICKNESS * 1.1):
        assert segment.get_burn_area(web_distance) == 0.0
        assert segment.get_volume(web_distance) == 0.0
