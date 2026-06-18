import pytest

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.core.compressible_flow.nozzle as core_nozzle


def test_get_optimal_expansion_ratio():
    k = 1.15
    chamber_pressure = 6.4e6
    external_pressure = 1e5
    optimal_expansion_ratio = core_nozzle.get_optimal_expansion_ratio(
        k, chamber_pressure, external_pressure
    )

    assert optimal_expansion_ratio == pytest.approx(9.37, rel=1e-2)


def test_get_separated_exit_conditions_attached():
    # High chamber pressure: the nozzle flows full and conditions are unchanged.
    k_exhaust = 1.2
    expansion_ratio = 8.0
    chamber_pressure = 7e6
    external_pressure = 1e5
    effective_expansion_ratio, exit_pressure = (
        core_nozzle.get_separated_exit_conditions(
            k_exhaust, expansion_ratio, chamber_pressure, external_pressure, 0.4
        )
    )

    assert effective_expansion_ratio == expansion_ratio
    assert exit_pressure == pytest.approx(
        isentropic.get_exit_pressure(k_exhaust, expansion_ratio, chamber_pressure)
    )


def test_get_separated_exit_conditions_separated():
    # Low chamber pressure: the flow separates upstream of the geometric exit.
    k_exhaust = 1.2
    expansion_ratio = 8.0
    chamber_pressure = 3e5
    external_pressure = 1e5
    separation_pressure_ratio = 0.4
    effective_expansion_ratio, exit_pressure = (
        core_nozzle.get_separated_exit_conditions(
            k_exhaust,
            expansion_ratio,
            chamber_pressure,
            external_pressure,
            separation_pressure_ratio,
        )
    )

    assert 1.0 < effective_expansion_ratio < expansion_ratio
    assert exit_pressure == pytest.approx(separation_pressure_ratio * external_pressure)


def test_get_separated_exit_conditions_unchoked_limit():
    # Near-ambient chamber pressure: separation reaches the throat, so the
    # effective exit collapses to sonic conditions.
    k_exhaust = 1.2
    expansion_ratio = 8.0
    chamber_pressure = 6e4
    external_pressure = 1e5
    effective_expansion_ratio, exit_pressure = (
        core_nozzle.get_separated_exit_conditions(
            k_exhaust, expansion_ratio, chamber_pressure, external_pressure, 0.4
        )
    )

    assert effective_expansion_ratio == 1.0
    assert exit_pressure == pytest.approx(
        chamber_pressure * isentropic.get_critical_pressure_ratio(k_exhaust)
    )


@pytest.mark.parametrize(
    "external_pressure, expected_pressure_term",
    [
        pytest.param(1e5, 0.022857142857142857, id="under_expanded"),
        pytest.param(1.2e5, 0.0, id="perfectly_expanded"),
        pytest.param(2e5, -0.09142857142857143, id="over_expanded"),
    ],
)
def test_get_ideal_thrust_coefficient_components(
    external_pressure, expected_pressure_term
):
    chamber_pressure = 7e6
    exit_pressure = 1.2e5
    expansion_ratio = 8.0
    k_exhaust = 1.4
    momentum_term, pressure_term = core_nozzle.get_ideal_thrust_coefficient_components(
        chamber_pressure,
        exit_pressure,
        external_pressure,
        expansion_ratio,
        k_exhaust,
    )

    # The momentum term depends only on the pressure ratio, so it is the same
    # across expansion conditions; only the pressure term changes sign.
    assert momentum_term == pytest.approx(1.5016496568524347)
    assert pressure_term == pytest.approx(expected_pressure_term)
    assert pressure_term == pytest.approx(
        expansion_ratio * (exit_pressure - external_pressure) / chamber_pressure
    )


def test_apply_thrust_coefficient_correction():
    ideal_thrust_coefficient = 1.524507
    nozzle_correction_factor = 0.8
    thrust_coefficient = core_nozzle.apply_thrust_coefficient_correction(
        ideal_thrust_coefficient, nozzle_correction_factor
    )

    assert thrust_coefficient == pytest.approx(1.219605)


def test_get_thrust_from_thrust_coefficient():
    thrust_coefficient = 1.6
    chamber_pressure = 7e6
    nozzle_throat_area = 0.01
    thrust = core_nozzle.get_thrust_from_thrust_coefficient(
        thrust_coefficient, chamber_pressure, nozzle_throat_area
    )

    assert thrust == pytest.approx(112000, rel=1e-2)
