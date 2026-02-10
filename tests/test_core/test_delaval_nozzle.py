from pytest import approx

from machwave.core.compressible_flow.delaval_nozzle import (
    apply_thrust_coefficient_correction,
    get_ideal_thrust_coefficient,
    get_optimal_expansion_ratio,
)


def test_get_optimal_expansion_ratio():
    k = 1.15
    P_0 = 6.4e6
    P_ext = 1e5
    exp_opt = get_optimal_expansion_ratio(k, P_0, P_ext)

    assert exp_opt == approx(9.37, rel=1e-2)


def test_get_ideal_thrust_coefficient():
    P_0 = 7e6
    P_exit = 1.2e5
    P_external = 1e5
    E = 8
    k = 1.4
    Cf_ideal = get_ideal_thrust_coefficient(P_0, P_exit, P_external, E, k)

    assert Cf_ideal == approx(1.524507)


def test_apply_thrust_coefficient_correction():
    Cf_ideal = 1.524507
    n_cf = 0.8
    Cf = apply_thrust_coefficient_correction(Cf_ideal, n_cf)

    assert Cf == approx(1.219605)
