"""Mass flux passes the tightest cross section of a segment, not its aft end.

The port area of a 3D segment varies along its length, so the mass flux has to
be evaluated at the bottleneck. Reading the aft end instead understates it,
badly for a tapered bore whose exposed end face reads as fully open.
"""

import numpy as np
import pytest

import machwave.models.grain as grain_models
from tests.factories import ConicalGrainSegmentFactory, StarGrainSegmentFactory

LENGTH = 68e-3
OUTER_DIAMETER = 41e-3
LOWER_CORE_DIAMETER = 30e-3  # aft (nozzle) end
UPPER_CORE_DIAMETER = 8e-3  # forward (bulkhead) end

IDEAL_DENSITY = 1750.0
BURN_RATE = np.array([0.005])
WEB_DISTANCE = np.array([0.002])


@pytest.fixture(scope="module")
def tapered_segment():
    return ConicalGrainSegmentFactory.build(
        length=LENGTH,
        outer_diameter=OUTER_DIAMETER,
        upper_core_diameter=UPPER_CORE_DIAMETER,
        lower_core_diameter=LOWER_CORE_DIAMETER,
    )


def test_minimum_port_area_matches_the_tightest_station(tapered_segment):
    web_distance = float(WEB_DISTANCE[0])
    stations = np.linspace(
        0.0, tapered_segment.length, tapered_segment.get_axial_resolution()
    )

    tightest = min(
        tapered_segment.get_port_area(web_distance, float(z)) for z in stations
    )

    assert tapered_segment.get_minimum_port_area(web_distance) == pytest.approx(
        tightest
    )
    assert tapered_segment.get_minimum_port_area(web_distance) < (
        tapered_segment.get_port_area(web_distance)
    )


def test_mass_flux_uses_the_bottleneck_port_area(tapered_segment):
    grain = grain_models.Grain(spacing=0.0)
    grain.add_segment(tapered_segment)

    mass_flux = grain.get_mass_flux_per_segment(BURN_RATE, IDEAL_DENSITY, WEB_DISTANCE)

    web_distance = float(WEB_DISTANCE[0])
    mass_flow_rate = (
        tapered_segment.get_burn_area(web_distance) * IDEAL_DENSITY * BURN_RATE[0]
    )
    expected = mass_flow_rate / tapered_segment.get_minimum_port_area(web_distance)
    aft_end_flux = mass_flow_rate / tapered_segment.get_port_area(web_distance)

    assert mass_flux[0, 0] == pytest.approx(expected)
    assert mass_flux[0, 0] > aft_end_flux


def test_uniform_segment_bottleneck_is_its_port_area():
    segment = StarGrainSegmentFactory.build(length=0.2, outer_diameter=OUTER_DIAMETER)
    web_distance = float(WEB_DISTANCE[0])

    assert segment.get_minimum_port_area(web_distance) == pytest.approx(
        segment.get_port_area(web_distance)
    )
