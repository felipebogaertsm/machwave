from pytest import approx

from machwave.core.compressible_flow.thrust import (
    get_thrust_coefficient_from_thrust,
    get_thrust_from_thrust_coefficient,
)
from machwave.core.propulsion import get_specific_impulse, get_total_impulse


def test_get_thrust_from_thrust_coefficient():
    C_f = 1.6
    P_0 = 7e6
    nozzle_throat_area = 0.01
    thrust = get_thrust_from_thrust_coefficient(C_f, P_0, nozzle_throat_area)

    assert thrust == approx(112000, rel=1e-2)


def test_get_thrust_coefficient_from_thrust():
    chamber_pressure = 7e6
    thrust = 112000
    nozzle_throat_area = 0.01
    thrust_coefficient = get_thrust_coefficient_from_thrust(
        chamber_pressure, thrust, nozzle_throat_area
    )

    assert thrust_coefficient == approx(1.6)


def test_get_total_impulse():
    average_thrust = 1000
    thrust_time = 2.5
    total_impulse = get_total_impulse(average_thrust, thrust_time)
    assert total_impulse == approx(2500)


def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = get_specific_impulse(total_impulse, initial_propellant_mass)
    assert specific_impulse == approx(2.542, rel=1e-2)
