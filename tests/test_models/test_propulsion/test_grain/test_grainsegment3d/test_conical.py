"""
NOTE: Due to the nature of the FMM algorithm, the results of this test are
dependent on the map_dim parameter. The higher the map_dim, the more accurate
the results will be, but the slower the algorithm will be.

To compensate for this imprecision, the tolerance is set to 10% of the expected
value. Also, the tests only run for a web distance up to 80% of the web
thickness, since the FMM algorithm is not accurate enough (given the lower 
map_dim) for the last 20% of the web thickness.
"""

import pytest

import numpy as np

from machwave.models.propulsion.grain.geometries import (
    BatesSegment,
    ConicalGrainSegment,
)

TOLERANCE = 0.10  # 10% tolerance
WEB_DISTANCE_TRAVEL_PERCENTAGE = 0.8  # 80% of the web thickness
NUMBER_OF_ITERATIONS = 3  # Number of iterations for the test


@pytest.fixture
def conical_grain_segment_1():
    return ConicalGrainSegment(
        length=68e-3,
        outer_diameter=41e-3,
        upper_core_diameter=15e-3,
        lower_core_diameter=15e-3,
        spacing=0.01,
    )


@pytest.fixture
def bates_equivalent_1():
    return BatesSegment(
        length=68e-3,
        outer_diameter=41e-3,
        core_diameter=15e-3,
        spacing=0.01,
    )


def test_burn_area(conical_grain_segment_1, bates_equivalent_1):
    web_thickness = conical_grain_segment_1.get_web_thickness()

    for web_distance in np.linspace(
        0, web_thickness * WEB_DISTANCE_TRAVEL_PERCENTAGE, NUMBER_OF_ITERATIONS
    ):
        value = conical_grain_segment_1.get_burn_area(web_distance)

        assert isinstance(
            value, float
        ), f"Expected float, but got {type(value)}"

        # Asserting that the burn area is the same as the bates equivalent:
        expected_value = bates_equivalent_1.get_burn_area(web_distance)
        tolerance = expected_value * TOLERANCE

        assert value == pytest.approx(
            expected_value, abs=tolerance
        ), f"Expected value {expected_value} with tolerance {tolerance}, but got {value} for web_distance {web_distance} out of {web_thickness}"


def test_port_area(conical_grain_segment_1, bates_equivalent_1):
    value = conical_grain_segment_1.get_port_area(0)

    assert isinstance(value, float), f"Expected float, but got {type(value)}"

    # Asserting that the burn area is the same as the bates equivalent:
    expected_value = bates_equivalent_1.get_port_area(0)
    tolerance = expected_value * TOLERANCE * 2

    assert value == pytest.approx(
        expected_value, abs=tolerance
    ), f"Expected value {expected_value} with tolerance {tolerance}"
