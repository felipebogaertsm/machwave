import pytest

import machwave.core.compressible_flow.isentropic as isentropic


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


@pytest.mark.parametrize("k", [1.15, 1.2, 1.4])
@pytest.mark.parametrize("expansion_ratio", [1.0 + 1e-9, 1.001, 1.5, 8.0, 100.0])
def test_get_exit_mach_from_expansion_ratio_round_trip(k, expansion_ratio):
    exit_mach = isentropic.get_exit_mach_from_expansion_ratio(k, expansion_ratio)

    assert exit_mach > 1.0
    assert isentropic.get_expansion_ratio_from_exit_mach(exit_mach, k) == pytest.approx(
        expansion_ratio
    )


def test_get_exit_mach_from_expansion_ratio_at_throat():
    for branch in isentropic.FlowBranch:
        assert isentropic.get_exit_mach_from_expansion_ratio(1.2, 1.0, branch) == 1.0


def test_get_exit_mach_from_expansion_ratio_below_throat():
    with pytest.raises(ValueError, match="no supersonic solution"):
        isentropic.get_exit_mach_from_expansion_ratio(1.2, 0.999)


def test_get_exit_mach_from_expansion_ratio_above_mach_limit():
    k = 1.4
    maximum_expansion_ratio = isentropic.get_maximum_expansion_ratio(
        k, isentropic.FlowBranch.SUPERSONIC
    )

    with pytest.raises(ValueError) as excinfo:
        isentropic.get_exit_mach_from_expansion_ratio(k, 2 * maximum_expansion_ratio)

    message = str(excinfo.value)
    assert "supersonic branch covers expansion ratios" in message
    assert "sonic throat" in message
    assert f"{maximum_expansion_ratio:.6g}" in message

    assert isentropic.get_exit_mach_from_expansion_ratio(
        k, maximum_expansion_ratio
    ) == pytest.approx(20.0)


def test_get_exit_mach_from_expansion_ratio_subsonic_branch():
    k = 1.2
    expansion_ratio = 8.0
    subsonic_mach = isentropic.get_exit_mach_from_expansion_ratio(
        k, expansion_ratio, isentropic.FlowBranch.SUBSONIC
    )

    assert subsonic_mach < 1.0
    assert isentropic.get_expansion_ratio_from_exit_mach(
        subsonic_mach, k
    ) == pytest.approx(expansion_ratio)
    assert subsonic_mach != pytest.approx(
        isentropic.get_exit_mach_from_expansion_ratio(k, expansion_ratio)
    )


def test_get_exit_mach_from_expansion_ratio_subsonic_branch_above_mach_limit():
    k = 1.2
    branch = isentropic.FlowBranch.SUBSONIC
    maximum_expansion_ratio = isentropic.get_maximum_expansion_ratio(k, branch)

    with pytest.raises(ValueError, match="no subsonic solution"):
        isentropic.get_exit_mach_from_expansion_ratio(
            k, 2 * maximum_expansion_ratio, branch
        )


def test_get_exit_pressure():
    k_exhaust = 1.4
    expansion_ratio = 8.0
    chamber_pressure = 7e6
    exit_pressure = isentropic.get_exit_pressure(
        k_exhaust, expansion_ratio, chamber_pressure
    )

    assert exit_pressure == pytest.approx(71545.88, rel=1e-2)


def test_get_exit_pressure_at_throat_is_sonic():
    k_exhaust = 1.2
    chamber_pressure = 7e6
    exit_pressure = isentropic.get_exit_pressure(k_exhaust, 1.0, chamber_pressure)

    assert exit_pressure == pytest.approx(
        chamber_pressure * isentropic.get_critical_pressure_ratio(k_exhaust)
    )


def test_get_exit_pressure_subsonic_branch():
    # An unstarted nozzle leaves subsonically and barely drops below chamber pressure.
    k_exhaust = 1.2
    expansion_ratio = 8.0
    chamber_pressure = 7e6
    subsonic_exit_pressure = isentropic.get_exit_pressure(
        k_exhaust, expansion_ratio, chamber_pressure, isentropic.FlowBranch.SUBSONIC
    )
    supersonic_exit_pressure = isentropic.get_exit_pressure(
        k_exhaust, expansion_ratio, chamber_pressure
    )

    assert subsonic_exit_pressure == pytest.approx(chamber_pressure, rel=1e-2)
    assert supersonic_exit_pressure < 0.1 * subsonic_exit_pressure


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
