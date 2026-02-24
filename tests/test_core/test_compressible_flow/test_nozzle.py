import pytest

import machwave.core.compressible_flow.nozzle as core_nozzle


def test_get_optimal_expansion_ratio():
    k = 1.15
    P_0 = 6.4e6
    P_ext = 1e5
    exp_opt = core_nozzle.get_optimal_expansion_ratio(k, P_0, P_ext)

    assert exp_opt == pytest.approx(9.37, rel=1e-2)


def test_get_ideal_thrust_coefficient():
    P_0 = 7e6
    P_exit = 1.2e5
    P_external = 1e5
    E = 8.0
    k = 1.4
    Cf_ideal = core_nozzle.get_ideal_thrust_coefficient(P_0, P_exit, P_external, E, k)

    assert Cf_ideal == pytest.approx(1.524507)


def test_apply_thrust_coefficient_correction():
    Cf_ideal = 1.524507
    n_cf = 0.8
    Cf = core_nozzle.apply_thrust_coefficient_correction(Cf_ideal, n_cf)

    assert Cf == pytest.approx(1.219605)


def test_get_thrust_from_thrust_coefficient():
    C_f = 1.6
    P_0 = 7e6
    nozzle_throat_area = 0.01
    thrust = core_nozzle.get_thrust_from_thrust_coefficient(
        C_f, P_0, nozzle_throat_area
    )

    assert thrust == pytest.approx(112000, rel=1e-2)
