import numpy as np
import pytest

import machwave.core.performance as core_performance


def test_get_total_impulse_constant_thrust():
    thrust = np.array([500.0, 500.0, 500.0])
    time = np.array([0.0, 1.0, 2.0])
    impulse = core_performance.get_total_impulse(thrust, time)
    assert impulse == pytest.approx(1000.0)


def test_get_total_impulse_linear_ramp():
    thrust = np.array([0.0, 1000.0])
    time = np.array([0.0, 2.0])
    impulse = core_performance.get_total_impulse(thrust, time)
    assert impulse == pytest.approx(1000.0)


def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = core_performance.get_specific_impulse(
        total_impulse, initial_propellant_mass
    )
    assert specific_impulse == pytest.approx(2.542, rel=1e-2)


def test_get_specific_impulse_is_nan_when_no_propellant_was_expelled():
    assert np.isnan(core_performance.get_specific_impulse(2500.0, 0.0))


def test_effective_flame_temperature_unity_efficiency_is_unchanged():
    """An efficiency of 1.0 returns the flame temperature untouched."""
    assert core_performance.get_effective_flame_temperature(
        adiabatic_flame_temperature=2_800.0, combustion_efficiency=1.0
    ) == pytest.approx(2_800.0)


@pytest.mark.parametrize(
    "combustion_efficiency, adiabatic_flame_temperature, expected",
    [
        (0.95, 2_800.0, 0.95**2 * 2_800.0),
        (0.5, 2_800.0, 700.0),
    ],
)
def test_effective_flame_temperature_squares_the_characteristic_velocity_efficiency(
    combustion_efficiency, adiabatic_flame_temperature, expected
):
    assert core_performance.get_effective_flame_temperature(
        adiabatic_flame_temperature=adiabatic_flame_temperature,
        combustion_efficiency=combustion_efficiency,
    ) == pytest.approx(expected)
