import pytest

import machwave.core.performance as core_performance


def test_get_total_impulse():
    average_thrust = 1000
    thrust_time = 2.5
    total_impulse = core_performance.get_total_impulse(average_thrust, thrust_time)
    assert total_impulse == pytest.approx(2500)


def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = core_performance.get_specific_impulse(
        total_impulse, initial_propellant_mass
    )
    assert specific_impulse == pytest.approx(2.542, rel=1e-2)
