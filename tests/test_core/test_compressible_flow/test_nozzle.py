import pytest

import machwave.core.compressible_flow.nozzle as core_nozzle


def test_get_optimal_expansion_ratio():
    k = 1.15
    chamber_pressure = 6.4e6
    external_pressure = 1e5
    optimal_expansion_ratio = core_nozzle.get_optimal_expansion_ratio(
        k, chamber_pressure, external_pressure
    )

    assert optimal_expansion_ratio == pytest.approx(9.37, rel=1e-2)


def test_get_ideal_thrust_coefficient():
    chamber_pressure = 7e6
    exit_pressure = 1.2e5
    external_pressure = 1e5
    expansion_ratio = 8.0
    k_exhaust = 1.4
    thrust_coefficient_ideal = core_nozzle.get_ideal_thrust_coefficient(
        chamber_pressure,
        exit_pressure,
        external_pressure,
        expansion_ratio,
        k_exhaust,
    )

    assert thrust_coefficient_ideal == pytest.approx(1.524507)


def test_apply_thrust_coefficient_correction():
    thrust_coefficient_ideal = 1.524507
    nozzle_correction_factor = 0.8
    thrust_coefficient = core_nozzle.apply_thrust_coefficient_correction(
        thrust_coefficient_ideal, nozzle_correction_factor
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
