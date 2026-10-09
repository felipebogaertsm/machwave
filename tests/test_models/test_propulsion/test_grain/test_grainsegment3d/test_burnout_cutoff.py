"""Volume is zero wherever the mass properties of a 3D FMM segment are undefined."""

import numpy as np
import pytest

import machwave.models.grain.geometries as grain_geometries

IDEAL_DENSITY = 1800.0


@pytest.fixture(scope="module")
def segment():
    return grain_geometries.FinocylGrainSegment(
        length=0.03,
        outer_diameter=0.09,
        core_diameter=0.033,
        number_of_fins=4,
        fin_length=0.022,
        fin_width=0.006,
        finned_length=0.03,
    )


def test_volume_is_zero_at_and_past_the_web_thickness(segment):
    web_thickness = segment.get_web_thickness()
    for web_distance in (web_thickness, np.nextafter(web_thickness, np.inf)):
        assert segment.get_volume(float(web_distance)) == 0.0


def test_mass_properties_are_defined_wherever_volume_is_positive(segment):
    web_thickness = segment.get_web_thickness()
    for web_distance in np.linspace(0.95 * web_thickness, 1.05 * web_thickness, 41):
        if segment.get_volume(float(web_distance)) > 0.0:
            segment.get_center_of_gravity(float(web_distance))
            segment.get_moment_of_inertia(IDEAL_DENSITY, float(web_distance))
