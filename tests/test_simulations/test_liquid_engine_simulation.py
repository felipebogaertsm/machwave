"""End-to-end integration tests for LiquidEngine internal ballistics
simulations.

Driven by the lone biliquid example (examples/lre_1kn.py). Like its solid
counterpart, the example exposes a build() function returning (motor, params).
The simulation is module-scoped so all assertions share a single run.
"""

from __future__ import annotations

import numpy as np
import pytest

from examples.lre_1kn import build as build_1kn_lre
from machwave.states import LiquidEngineState
from tests.test_simulations.conftest import (
    SimulationResult,
    assert_recorded_arrays_aligned,
    run_simulation,
)


@pytest.fixture(scope="module")
def simulation_result() -> SimulationResult:
    motor, params = build_1kn_lre()
    return run_simulation(motor, params)


def test_simulation_completes_with_terminal_state(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert isinstance(state, LiquidEngineState)
    assert state.end_thrust is True
    assert simulation_result.time.size == len(state.t)
    assert simulation_result.time.size > 1


def test_burn_time_and_thrust_time_are_finite_and_ordered(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert np.isfinite(state.burn_time)
    assert np.isfinite(state.thrust_time)
    assert state.burn_time > 0.0
    assert state.thrust_time >= state.burn_time


def test_propellant_masses_are_monotone_non_increasing(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    for series_name in ("fuel_mass", "oxidizer_mass", "m_prop"):
        series = np.asarray(getattr(state, series_name))
        diffs = np.diff(series)
        assert (diffs <= 1e-9).all(), (
            f"{series_name} increased between steps; max delta={diffs.max():.3e}"
        )
        assert series[-1] <= series[0]


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    peak_pressure = float(np.max(state.P_0))
    peak_thrust = float(np.max(state.thrust))
    # A 1 kN-class biliquid engine should peak at 0.5 to 5 MPa chamber pressure
    # and produce on the order of 100 N to 10 kN of peak thrust.
    assert 0.5e6 < peak_pressure < 5.0e6, (
        f"peak chamber pressure {peak_pressure:.2e} Pa outside [5e5, 5e6]"
    )
    assert 100.0 < peak_thrust < 1.0e4, (
        f"peak thrust {peak_thrust:.2e} N outside [100, 1e4]"
    )


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: SimulationResult,
) -> None:
    assert_recorded_arrays_aligned(
        simulation_result.state,
        attribute_names=(
            "P_0",
            "P_exit",
            "thrust",
            "C_f",
            "C_f_ideal",
            "fuel_mass",
            "oxidizer_mass",
            "m_prop",
            "n_cf",
            "fuel_tank_pressure",
            "oxidizer_tank_pressure",
        ),
    )
