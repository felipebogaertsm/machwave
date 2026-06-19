"""
End-to-end integration tests for BiliquidEngine internal ballistics
simulations.

The motor configuration lives in tests/test_simulations/motor_builders.py so
it can be reused by benchmarks under tests/benchmarks/.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import machwave.models.motors as motors_models
import machwave.simulation.biliquid as biliquid_simulation
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import (
    assert_recorded_arrays_aligned,
    run_simulation,
)


@pytest.fixture(scope="module")
def simulated_motor_and_result() -> tuple[
    motors_models.BiliquidEngine, biliquid_simulation.BiliquidSimulationResult
]:
    motor, params = motor_builders.build_1kn_biliquid_engine()
    return motor, run_simulation(motor, params)


@pytest.fixture(scope="module")
def simulation_result(
    simulated_motor_and_result: tuple[
        motors_models.BiliquidEngine, biliquid_simulation.BiliquidSimulationResult
    ],
) -> biliquid_simulation.BiliquidSimulationResult:
    return simulated_motor_and_result[1]


def test_simulation_completes_with_terminal_state(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    assert isinstance(simulation_result, biliquid_simulation.BiliquidSimulationResult)
    assert simulation_result.end_thrust is True
    assert simulation_result.time.size > 1


def test_thrust_time_is_finite_and_positive(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    assert np.isfinite(simulation_result.thrust_time)
    assert simulation_result.thrust_time > 0.0


def test_motor_is_re_runnable() -> None:
    """A motor must produce identical results when simulated twice.

    Regression test for #321: the tank used to be drained in place during a
    run, so a second run started from an empty tank. With the tank stateless and
    the mass owned by the simulation state, re-running is reproducible.
    """
    motor, params = motor_builders.build_1kn_biliquid_engine()

    first = run_simulation(motor, params)
    second = run_simulation(motor, params)

    assert first.time.size == second.time.size
    np.testing.assert_array_equal(first.oxidizer_mass, second.oxidizer_mass)
    np.testing.assert_array_equal(first.fuel_mass, second.fuel_mass)
    np.testing.assert_array_equal(first.thrust, second.thrust)


def test_propellant_masses_are_monotone_non_increasing(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
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
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
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
    # Flow separation bounds the overexpanded pressure-thrust term, so thrust
    # stays non-negative through tail-off.
    min_thrust = float(np.min(simulation_result.thrust))
    assert min_thrust >= 0.0, f"thrust dips negative: {min_thrust:.2e} N"


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    assert_recorded_arrays_aligned(simulation_result)


def test_loss_fraction_series_match_model_components(
    simulated_motor_and_result: tuple[
        motors_models.BiliquidEngine, biliquid_simulation.BiliquidSimulationResult
    ],
) -> None:
    """The result exposes one named, in-range loss series per model component."""
    motor, result = simulated_motor_and_result
    component_names = set(motor.nozzle_loss_model.component_names)
    assert set(result.loss_fractions) == component_names
    assert set(result.loss_labels) == component_names
    for series in result.loss_fractions.values():
        assert np.all(np.isfinite(series))
        assert np.all((series >= 0.0) & (series <= 1.0))


def test_thrust_coefficient_is_ideal_times_nozzle_efficiency(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    # The recorded thrust coefficient must be the corrected (derated) terms, so it
    # equals the ideal coefficient scaled by the realized nozzle efficiency.
    np.testing.assert_allclose(
        simulation_result.thrust_coefficient,
        simulation_result.ideal_thrust_coefficient
        * simulation_result.nozzle_efficiency,
        rtol=1e-9,
    )


def test_thrust_equals_thrust_coefficient_times_chamber_pressure_times_throat_area(
    simulated_motor_and_result: tuple[
        motors_models.BiliquidEngine, biliquid_simulation.BiliquidSimulationResult
    ],
) -> None:
    motor, result = simulated_motor_and_result
    throat_area = motor.thrust_chamber.nozzle.get_throat_area()
    np.testing.assert_allclose(
        result.thrust,
        result.thrust_coefficient * result.chamber_pressure * throat_area,
        rtol=1e-9,
    )


def test_exit_pressure_is_finite_and_positive(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    assert np.all(np.isfinite(simulation_result.exit_pressure))
    assert np.all(simulation_result.exit_pressure > 0.0)


def _build_state_for_burnout_test() -> biliquid_simulation.BiliquidEngineState:
    motor, params = motor_builders.build_1kn_biliquid_engine()
    return biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
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


def test_live_mixture_ratio_drives_cea() -> None:
    motor, params = motor_builders.build_1kn_biliquid_engine()
    state = biliquid_simulation.BiliquidEngineState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )

    design_ratio = motor.propellant.oxidizer_to_fuel_ratio
    assert design_ratio is not None

    deviation_sample: tuple[float, float] | None = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        while not state.end_thrust:
            state.run_timestep(params.d_t, params.external_pressure)
            if state.fuel_mass_flow_rate[-1] <= 0.0:
                continue
            live_ratio = state.oxidizer_to_fuel_ratio[-1]
            if abs(live_ratio - design_ratio) > 1e-6:
                deviation_sample = (live_ratio, state.chamber_pressure[-1])

    assert deviation_sample is not None, (
        "Live oxidizer/fuel mass flow ratio never deviated from the design ratio"
    )
    live_ratio, live_chamber_pressure = deviation_sample

    live_props = motor.propellant.evaluate(
        chamber_pressure=live_chamber_pressure,
        expansion_ratio=motor.thrust_chamber.nozzle.expansion_ratio,
        mixture_ratio=live_ratio,
    )
    design_props = motor.propellant.evaluate(
        chamber_pressure=live_chamber_pressure,
        expansion_ratio=motor.thrust_chamber.nozzle.expansion_ratio,
        mixture_ratio=design_ratio,
    )
    assert (
        live_props.adiabatic_flame_temperature
        != design_props.adiabatic_flame_temperature
    )


def test_simulation_runs_through_burnout_without_crashing(
    simulation_result: biliquid_simulation.BiliquidSimulationResult,
) -> None:
    assert simulation_result.end_thrust is True
    assert simulation_result.propellant_mass[-1] <= simulation_result.propellant_mass[0]


def test_combustion_efficiency_derates_chamber_not_thrust_coefficient() -> None:
    """Combustion efficiency acts on the chamber side, not the thrust coefficient.

    The nozzle efficiency applied to the thrust coefficient depends only on
    geometry and nozzle losses, so it is independent of the motor's combustion
    efficiency. Combustion efficiency instead derates the flame temperature fed
    to the chamber-pressure solver, so the chamber-pressure path responds to it.
    """

    def first_step(
        combustion_efficiency: float,
    ) -> biliquid_simulation.BiliquidEngineState:
        motor, params = motor_builders.build_1kn_biliquid_engine()
        motor.combustion_efficiency = combustion_efficiency
        state = biliquid_simulation.BiliquidEngineState(
            motor=motor,
            igniter_pressure=params.igniter_pressure,
            external_pressure=params.external_pressure,
        )
        state.run_timestep(d_t=params.d_t, external_pressure=params.external_pressure)
        return state

    full = first_step(1.0)
    derated = first_step(0.5)

    assert derated.nozzle_efficiency[-1] == pytest.approx(full.nozzle_efficiency[-1])
    assert derated.chamber_pressure[-1] != pytest.approx(full.chamber_pressure[-1])
