import numpy as np
import pytest

import machwave.core.performance as core_performance


def test_get_total_impulse():
    average_thrust = 1000
    thrust_time = 2.5
    total_impulse = core_performance.get_total_impulse(average_thrust, thrust_time)
    assert total_impulse == pytest.approx(2500)


def test_get_total_impulse_trapezoidal_constant_thrust_matches_rectangular():
    thrust = np.array([500.0, 500.0, 500.0])
    time = np.array([0.0, 1.0, 2.0])
    impulse = core_performance.get_total_impulse_trapezoidal(thrust, time)
    assert impulse == pytest.approx(1000.0)


def test_get_total_impulse_trapezoidal_linear_ramp():
    thrust = np.array([0.0, 1000.0])
    time = np.array([0.0, 2.0])
    impulse = core_performance.get_total_impulse_trapezoidal(thrust, time)
    assert impulse == pytest.approx(1000.0)


def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = core_performance.get_specific_impulse(
        total_impulse, initial_propellant_mass
    )
    assert specific_impulse == pytest.approx(2.542, rel=1e-2)
