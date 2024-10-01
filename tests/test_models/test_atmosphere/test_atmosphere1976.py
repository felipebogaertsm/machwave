from typing import Callable

import numpy as np
from numpy import testing as np_testing
import pytest

from machwave.models.atmosphere import Atmosphere
from machwave.models.atmosphere.atm_1976 import (
    Atmosphere1976,
    Atmosphere1976WindPowerLaw,
)


def test_atmosphere1976_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None]
) -> None:
    test_atmosphere_up_to_karman_line(atmosphere=Atmosphere1976())


def test_atmosphere1976_default_wind_velocity_yamsl_0():
    """
    Test that the default wind velocity is (7, 7) in Atmosphere1976.
    y_amsl = 0.
    """
    atmosphere1976 = Atmosphere1976()
    wind_velocity = atmosphere1976.get_wind_velocity(0)
    np_testing.assert_almost_equal(wind_velocity, (7, 7), decimal=5)


def test_atmosphere1976_default_wind_velocity_yamsl_500():
    """
    Test that the default wind velocity is (7, 7) in Atmosphere1976.
    y_amsl = 500.
    """
    atmosphere1976 = Atmosphere1976()
    wind_velocity = atmosphere1976.get_wind_velocity(500)
    np_testing.assert_almost_equal(wind_velocity, (7, 7), decimal=5)


def test_atmosphere1976windpowerlaw_z_ref_zero():
    """
    Test that an exception is raised when z_ref is set to 0 in
    Atmosphere1976WindPowerLaw.
    """
    with pytest.raises(
        ValueError,
        match="Please provide a non-zero reference height 'z_ref'.",
    ):
        Atmosphere1976WindPowerLaw(
            v_ref=7, z_ref=0, alpha=0.1, direction_deg=60
        )


def test_atmosphere1976windpowerlaw_up_to_karman_line(
    test_atmosphere_up_to_karman_line: Callable[[Atmosphere], None],
    atmosphere1976withwindpowerlaw: Atmosphere1976,
) -> None:
    test_atmosphere_up_to_karman_line(
        atmosphere=atmosphere1976withwindpowerlaw
    )


def test_get_wind_velocity_low_altitude(atmosphere1976withwindpowerlaw):
    """Test wind velocity at a low altitude using the power law."""
    northward, eastward = atmosphere1976withwindpowerlaw.get_wind_velocity(
        10.0
    )
    expected_speed = 7.0  # Since altitude is equal to reference height
    direction_rad = np.radians(60.0)
    expected_northward = expected_speed * np.cos(direction_rad)
    expected_eastward = expected_speed * np.sin(direction_rad)
    np_testing.assert_almost_equal(
        [northward, eastward],
        [expected_northward, expected_eastward],
        decimal=5,
    )


def test_get_wind_velocity_higher_altitude(atmosphere1976withwindpowerlaw):
    """Test wind velocity at a higher altitude using the power law."""
    northward, eastward = atmosphere1976withwindpowerlaw.get_wind_velocity(
        100.0
    )
    expected_speed = 7.0 * (100.0 / 10.0) ** 0.1  # Apply power law
    direction_rad = np.radians(60.0)
    expected_northward = expected_speed * np.cos(direction_rad)
    expected_eastward = expected_speed * np.sin(direction_rad)
    np_testing.assert_almost_equal(
        [northward, eastward],
        [expected_northward, expected_eastward],
        decimal=5,
    )


def test_get_wind_velocity_negative_altitude(atmosphere1976withwindpowerlaw):
    """Test wind velocity when given a negative altitude (should return wind at reference height)."""
    northward, eastward = atmosphere1976withwindpowerlaw.get_wind_velocity(
        -50.0
    )
    expected_speed = 7.0  # Should default to reference height speed
    direction_rad = np.radians(60.0)
    expected_northward = expected_speed * np.cos(direction_rad)
    expected_eastward = expected_speed * np.sin(direction_rad)
    np_testing.assert_almost_equal(
        [northward, eastward],
        [expected_northward, expected_eastward],
        decimal=5,
    )
