from pytest import approx

from machwave.core.flow.isentropic import (
    apply_thrust_coefficient_correction,
    get_critical_pressure_ratio,
    get_exit_mach,
    get_exit_pressure,
    get_ideal_thrust_coefficient,
    get_optimal_expansion_ratio,
    get_specific_impulse,
    get_thrust_from_thrust_coefficient,
    get_total_impulse,
    is_flow_choked,
)


def test_get_critical_pressure_ratio():
    k = 1.4
    critical_pressure_ratio = get_critical_pressure_ratio(k)

    assert critical_pressure_ratio == approx(0.528282)


def test_get_optimal_expansion_ratio():
    k = 1.15
    P_0 = 6.4e6
    P_ext = 1e5
    exp_opt = get_optimal_expansion_ratio(k, P_0, P_ext)

    assert exp_opt == approx(9.37, rel=1e-2)


def test_get_exit_mach():
    k = 1.4
    expansion_ratio = 8
    exit_mach = get_exit_mach(k, expansion_ratio)

    assert exit_mach == approx(3.677229)


def test_get_exit_pressure():
    k_ex = 1.4
    E = 8
    P_0 = 7e6
    P_exit = get_exit_pressure(k_ex, E, P_0)

    assert P_exit == approx(71545.88, rel=1e-2)


def test_get_thrust_coefficient():
    P_0 = 7e6
    P_exit = 1.2e5
    P_external = 1e5
    E = 8
    k = 1.4
    n_cf = 0.8
    Cf_ideal = get_ideal_thrust_coefficient(P_0, P_exit, P_external, E, k)
    Cf = apply_thrust_coefficient_correction(Cf_ideal, n_cf)

    assert Cf == approx(1.219605)
    assert Cf_ideal == approx(1.524507)


def test_get_thrust_from_thrust_coefficient():
    C_f = 1.6
    P_0 = 7e6
    nozzle_throat_area = 0.01
    thrust = get_thrust_from_thrust_coefficient(C_f, P_0, nozzle_throat_area)

    assert thrust == approx(112000, rel=1e-2)


def test_is_flow_choked():
    chamber_pressure = 7e6
    external_pressure = 1e5
    critical_pressure_ratio = 0.5

    # Flow is choked
    assert (
        is_flow_choked(chamber_pressure, external_pressure, critical_pressure_ratio)
        is True
    )

    # Flow is NOT choked
    assert is_flow_choked(external_pressure * 1.1, external_pressure, 0.5) is False


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
