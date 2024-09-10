import numpy as np

from pytest import approx, mark

from machwave.services.isentropic_flow import (
    get_critical_pressure_ratio,
    get_opt_expansion_ratio,
    get_exit_mach,
    get_exit_pressure,
    get_thrust_coefficients,
    get_thrust_from_cf,
    get_thrust_coefficient,
    is_flow_choked,
    get_impulses,
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


@mark.skip("Verify calculations")
def test_get_exit_mach():
    k = 1.4
    E = 8
    exit_mach = get_exit_mach(k, E)
    assert exit_mach == approx(1.51845024)


@mark.skip("Verify calculations")
def test_get_exit_pressure():
    k_2ph_ex = 1.4
    E = 0.99
    P_0 = 100000
    P_exit = get_exit_pressure(k_2ph_ex, E, P_0)
    assert P_exit == approx(10557.9996)


@mark.skip("Verify calculations")
def test_get_thrust_coefficients():
    P_0 = 100000
    P_exit = 90000
    P_external = 10000
    E = 0.99
    k = 1.4
    n_cf = 1.1
    Cf, Cf_ideal = get_thrust_coefficients(P_0, P_exit, P_external, E, k, n_cf)
    assert Cf == approx(0.296527)
    assert Cf_ideal == approx(0.272386)


@mark.skip("Verify calculations")
def test_get_thrust_from_cf():
    C_f = 0.3
    P_0 = 100000
    nozzle_throat_area = 0.01
    thrust = get_thrust_from_cf(C_f, P_0, nozzle_throat_area)
    assert thrust == approx(3000)


@mark.skip("Verify calculations")
def test_get_thrust_coefficient():
    P_0 = 100000
    thrust = 3000
    nozzle_throat_area = 0.01
    C_f = get_thrust_coefficient(P_0, thrust, nozzle_throat_area)
    assert C_f == approx(0.3)


@mark.skip("Verify calculations")
def test_is_flow_choked():
    chamber_pressure = 500000
    external_pressure = 100000
    critical_pressure_ratio = 0.5
    assert (
        is_flow_choked(
            chamber_pressure, external_pressure, critical_pressure_ratio
        )
        is False
    )
    assert is_flow_choked(200000, 100000, 0.5) is True
    assert is_flow_choked(100000, 200000, 0.5) is False


@mark.skip("Verify calculations")
def test_get_impulses():
    F_avg = 1000
    t = np.array([0, 1, 2, 3])
    t_burnout = 2.5
    m_prop = np.array([10, 8, 6, 4])
    I_total, I_sp = get_impulses(F_avg, t, t_burnout, m_prop)
    assert I_total == approx(5000)
    assert I_sp == approx(31.847)


@mark.skip("Verify calculations")
def test_get_total_impulse():
    average_thrust = 1000
    thrust_time = 2.5
    total_impulse = get_total_impulse(average_thrust, thrust_time)
    assert total_impulse == approx(2500)


@mark.skip("Verify calculations")
def test_get_specific_impulse():
    total_impulse = 2500
    initial_propellant_mass = 100
    specific_impulse = get_specific_impulse(
        total_impulse, initial_propellant_mass
    )
    assert specific_impulse == approx(2.542)


@mark.skip("Verify calculations")
def test_get_operational_correction_factors():
    P_0 = 100000
    P_external = 50000
    P_0_psi = 1450
    propellant = None  # Add appropriate propellant object here
    structure = None  # Add appropriate structure object here
    critical_pressure_ratio = 0.5
    V0 = 0.01
    t = 1
    n_kin, n_tp, n_bl = get_operational_correction_factors(
        P_0,
        P_external,
        P_0_psi,
        propellant,
        structure,
        critical_pressure_ratio,
        V0,
        t,
    )
    assert n_kin == approx(0)
    assert n_tp == approx(0)
    assert n_bl == approx(0)


@mark.skip("Verify calculations")
def test_get_divergent_correction_factor():
    divergent_angle = 15
    correction_factor = get_divergent_correction_factor(divergent_angle)
    assert correction_factor == approx(0.9659258262890683)


@mark.skip("Verify calculations")
def test_get_expansion_ratio():
    P_e = np.array([5000, 6000])
    P_0 = np.array([100000, 150000])
    k = 1.4
    critical_pressure_ratio = 0.5
    expansion_ratio = get_expansion_ratio(P_e, P_0, k, critical_pressure_ratio)
    assert expansion_ratio == approx(0.9090909090909091)
