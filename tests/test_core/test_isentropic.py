from pytest import approx

from machwave.core.compressible_flow.isentropic import (
    get_critical_pressure_ratio,
    get_exit_mach,
    get_exit_pressure,
    get_expansion_ratio_from_mach,
    is_flow_choked,
)


def test_get_critical_pressure_ratio():
    k = 1.4
    critical_pressure_ratio = get_critical_pressure_ratio(k)

    assert critical_pressure_ratio == approx(0.528282)


def test_get_expansion_ratio_from_mach():
    k = 1.4
    mach = 3.677229
    expansion_ratio = get_expansion_ratio_from_mach(mach, k)

    assert expansion_ratio == approx(8, rel=1e-4)


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
