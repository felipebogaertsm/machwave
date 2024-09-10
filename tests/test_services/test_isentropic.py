import numpy as np

from pytest import approx, mark

from machwave.services.isentropic_flow import (
    get_critical_pressure_ratio,
    get_opt_expansion_ratio,
    get_exit_mach,
    get_exit_pressure,
    get_thrust_coefficients,
    get_thrust_from_cf,
    is_flow_choked,
    get_total_impulse,
    get_specific_impulse,
    get_operational_correction_factors,
    get_divergent_correction_factor,
    get_expansion_ratio,
)


def test_get_critical_pressure_ratio():
    k_mix_ch = 1.4
    critical_pressure_ratio = get_critical_pressure_ratio(k_mix_ch)

    assert critical_pressure_ratio == approx(0.528282)


def test_get_opt_expansion_ratio():
    k = 1.15
    P_0 = 6.4e6
    P_ext = 1e5
    exp_opt = get_opt_expansion_ratio(k, P_0, P_ext)

    assert exp_opt == approx(9.37, rel=1e-2)


def test_get_exit_mach():
    k = 1.4
    expansion_ratio = 8
    exit_mach = get_exit_mach(k, expansion_ratio)

    assert exit_mach == approx(3.677229)


def test_get_exit_pressure():
    k_2ph_ex = 1.4
    E = 8
    P_0 = 7e6
    P_exit = get_exit_pressure(k_2ph_ex, E, P_0)

    assert P_exit == approx(71545.88, rel=1e-2)


def test_get_thrust_coefficients():
    P_0 = 7e6
    P_exit = 1.2e5
    P_external = 1e5
    E = 8
    k = 1.4
    n_cf = 0.8
    Cf, Cf_ideal = get_thrust_coefficients(P_0, P_exit, P_external, E, k, n_cf)

    assert Cf == approx(1.219605)
    assert Cf_ideal == approx(1.501650)


def test_get_thrust_from_cf():
    C_f = 1.6
    P_0 = 7e6
    nozzle_throat_area = 0.01
    thrust = get_thrust_from_cf(C_f, P_0, nozzle_throat_area)

    assert thrust == approx(112000, rel=1e-2)


def test_is_flow_choked():
    chamber_pressure = 7e6
    external_pressure = 1e5
    critical_pressure_ratio = 0.5

    # Flow is choked
    assert (
        is_flow_choked(
            chamber_pressure, external_pressure, critical_pressure_ratio
        )
        is True
    )

    # Flow is NOT choked
    assert (
        is_flow_choked(external_pressure * 1.1, external_pressure, 0.5)
        is False
    )


def test_get_total_impulse():
    average_thrust = 1000
    thrust_time = 2.5
    total_impulse = get_total_impulse(average_thrust, thrust_time)
    assert total_impulse == approx(2500)


def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = get_specific_impulse(
        total_impulse, initial_propellant_mass
    )
    assert specific_impulse == approx(2.542, rel=1e-2)


def test_get_divergent_correction_factor():
    divergent_angle = 15
    correction_factor = get_divergent_correction_factor(divergent_angle)
    assert correction_factor == approx(0.982962)


def test_get_expansion_ratio():
    P_e = np.array([5000, 6000])
    P_0 = np.array([100000, 150000])
    k = 1.4
    critical_pressure_ratio = 0.5
    expansion_ratio = get_expansion_ratio(P_e, P_0, k, critical_pressure_ratio)

    assert expansion_ratio == approx(3.11, rel=1e-2)
