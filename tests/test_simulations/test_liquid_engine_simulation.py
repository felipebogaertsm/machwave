"""
End-to-end integration tests for LiquidEngine internal ballistics
simulations.

The motor configuration lives in tests/test_simulations/motor_builders.py so
it can be reused by benchmarks under tests/benchmarks/.
"""

from __future__ import annotations

import numpy as np
import pytest

from machwave.models import motors
from machwave.simulation.liquid import LiquidEngineState, LiquidSimulationResult
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import (
    assert_recorded_arrays_aligned,
    run_simulation,
)


@pytest.fixture(scope="module")
def simulated_motor_and_result() -> tuple[motors.LiquidEngine, LiquidSimulationResult]:
    motor, params = motor_builders.build_1kn_lre()
    return motor, run_simulation(motor, params)


@pytest.fixture(scope="module")
def simulation_result(
    simulated_motor_and_result: tuple[motors.LiquidEngine, LiquidSimulationResult],
) -> LiquidSimulationResult:
    return simulated_motor_and_result[1]


def test_simulation_completes_with_terminal_state(
    simulation_result: LiquidSimulationResult,
) -> None:
    assert isinstance(simulation_result, LiquidSimulationResult)
    assert simulation_result.end_thrust is True
    assert simulation_result.time.size > 1


def test_thrust_time_is_finite_and_positive(
    simulation_result: LiquidSimulationResult,
) -> None:
    assert np.isfinite(simulation_result.thrust_time)
    assert simulation_result.thrust_time > 0.0


def test_propellant_masses_are_monotone_non_increasing(
    simulation_result: LiquidSimulationResult,
) -> None:
    for series_name in ("fuel_mass", "oxidizer_mass", "propellant_mass"):
        series = getattr(simulation_result, series_name)
        diffs = np.diff(series)
        assert (diffs <= 1e-9).all(), (
            f"{series_name} increased between steps; max delta={diffs.max():.3e}"
        )
        assert series[-1] <= series[0]
        assert (series >= -1e-9).all(), (
            f"{series_name} went negative; min={series.min():.3e}"
        )


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: LiquidSimulationResult,
) -> None:
    peak_pressure = float(np.max(simulation_result.chamber_pressure))
    peak_thrust = float(np.max(simulation_result.thrust))
    # A 1 kN-class biliquid engine should peak at 0.5 to 5 MPa chamber pressure
    # and produce on the order of 100 N to 10 kN of peak thrust.
    assert 0.5e6 < peak_pressure < 5.0e6, (
        f"peak chamber pressure {peak_pressure:.2e} Pa outside [5e5, 5e6]"
    )
    assert 100.0 < peak_thrust < 1.0e4, (
        f"peak thrust {peak_thrust:.2e} N outside [100, 1e4]"
    )


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: LiquidSimulationResult,
) -> None:
    assert_recorded_arrays_aligned(simulation_result)


def _build_state_for_burnout_test() -> LiquidEngineState:
    motor, params = motor_builders.build_1kn_lre()
    return LiquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
        other_losses=params.other_losses,
    )


def test_run_timestep_sets_end_burn_when_fuel_exhausts() -> None:
    state = _build_state_for_burnout_test()
    state.fuel_mass[-1] = 1e-9

    state.run_timestep(d_t=1e-4, external_pressure=1e5)

    assert state.end_burn is True
    assert state.burn_time == pytest.approx(state.time[-1])


def test_run_timestep_sets_end_burn_when_oxidizer_exhausts() -> None:
    state = _build_state_for_burnout_test()
    state.oxidizer_mass[-1] = 1e-9

    state.run_timestep(d_t=1e-4, external_pressure=1e5)

    assert state.end_burn is True
    assert state.burn_time == pytest.approx(state.time[-1])


def test_live_mixture_ratio_drives_cea(
    simulated_motor_and_result: tuple[motors.LiquidEngine, LiquidSimulationResult],
) -> None:
    motor, simulation_result = simulated_motor_and_result
    propellant = motor.propellant

    design_ratio = propellant.oxidizer_to_fuel_ratio
    assert design_ratio is not None

    fuel_consumed = -np.diff(simulation_result.fuel_mass)
    oxidizer_consumed = -np.diff(simulation_result.oxidizer_mass)
    valid = fuel_consumed > 0
    live_ratios = oxidizer_consumed[valid] / fuel_consumed[valid]
    assert np.any(np.abs(live_ratios - design_ratio) > 1e-6), (
        "Live oxidizer/fuel mass deltas never deviated from the design ratio"
    )

    chamber_pressure = simulation_result.chamber_pressure[
        len(simulation_result.chamber_pressure) // 2
    ]
    expansion_ratio = motor.thrust_chamber.nozzle.expansion_ratio
    design_props = propellant.evaluate(
        chamber_pressure=chamber_pressure,
        expansion_ratio=expansion_ratio,
        mixture_ratio=design_ratio,
    )
    live_props = propellant.properties
    assert live_props is not None
    assert (
        live_props.adiabatic_flame_temperature
        != design_props.adiabatic_flame_temperature
    )


def test_simulation_runs_through_burnout_without_crashing(
    simulation_result: LiquidSimulationResult,
) -> None:
    assert simulation_result.end_thrust is True
    assert simulation_result.propellant_mass[-1] <= simulation_result.propellant_mass[0]
