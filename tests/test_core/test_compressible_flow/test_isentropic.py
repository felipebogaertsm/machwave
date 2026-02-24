import pytest

from machwave.core.compressible_flow import isentropic


def test_get_critical_pressure_ratio():
    k = 1.4
    critical_pressure_ratio = isentropic.get_critical_pressure_ratio(k)

    assert critical_pressure_ratio == pytest.approx(0.528282)


def test_get_expansion_ratio_from_exit_mach():
    k = 1.4
    mach = 3.677229
    expansion_ratio = isentropic.get_expansion_ratio_from_exit_mach(mach, k)

    assert expansion_ratio == pytest.approx(8.0, rel=1e-4)


def test_get_exit_mach_from_expansion_ratio():
    k = 1.4
    expansion_ratio = 8.0
    exit_mach = isentropic.get_exit_mach_from_expansion_ratio(k, expansion_ratio)

    assert exit_mach == pytest.approx(3.677229)


def test_get_exit_pressure():
    k_ex = 1.4
    E = 8.0
    P_0 = 7e6
    P_exit = isentropic.get_exit_pressure(k_ex, E, P_0)

    assert P_exit == pytest.approx(71545.88, rel=1e-2)


def test_is_flow_choked_true():
    chamber_pressure = 7e6
    external_pressure = 1e5
    critical_pressure_ratio = 0.5

    assert isentropic.is_flow_choked(
        chamber_pressure, external_pressure, critical_pressure_ratio
    )


def test_is_flow_choked_false():
    chamber_pressure = 1.4e5
    external_pressure = 1e5
    critical_pressure_ratio = 0.5

    assert not isentropic.is_flow_choked(
        chamber_pressure, external_pressure, critical_pressure_ratio
    )
