"""End-to-end integration tests for SolidMotor internal ballistics simulations.

Each example under examples/ that builds a SolidMotor exposes a build()
function returning (motor, params). This module parameterizes the test suite
over those builders so adding a new example to the repo automatically gets
end-to-end coverage.
"""

from __future__ import annotations

import importlib
from typing import Callable

import numpy as np
import pytest

from machwave.models.motors import Motor
from machwave.simulation import InternalBallisticsSimulationParams
from machwave.states import SolidMotorState
from tests.test_simulations.conftest import (
    SimulationResult,
    assert_recorded_arrays_aligned,
    run_simulation,
)


SOLID_MOTOR_EXAMPLES: tuple[str, ...] = (
    "examples.apcp_motor",
    "examples.kappa_rnakka",
    "examples.nero_motor",
    "examples.olympus",
)


def _load_builder(
    example: str,
) -> Callable[[], tuple[Motor, InternalBallisticsSimulationParams]]:
    return importlib.import_module(example).build


@pytest.fixture(
    scope="module", params=SOLID_MOTOR_EXAMPLES, ids=lambda e: e.split(".")[-1]
)
def simulation_result(request: pytest.FixtureRequest) -> SimulationResult:
    motor, params = _load_builder(request.param)()
    return run_simulation(motor, params)


def test_simulation_completes_with_terminal_state(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert isinstance(state, SolidMotorState)
    assert state.end_thrust is True
    assert state.end_burn is True
    assert simulation_result.time.size == len(state.t)
    assert simulation_result.time.size > 1


def test_burn_time_and_thrust_time_are_finite_and_ordered(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    assert np.isfinite(state.burn_time)
    assert np.isfinite(state.thrust_time)
    assert state.burn_time > 0.0
    assert state.thrust_time > 0.0
    # Thrust persists at least until the burn ends, then decays once the
    # nozzle becomes unchoked.
    assert state.thrust_time >= state.burn_time


def test_propellant_mass_is_monotone_non_increasing(
    simulation_result: SimulationResult,
) -> None:
    m_prop = np.asarray(simulation_result.state.m_prop)
    diffs = np.diff(m_prop)
    # Allow tiny floating-point noise but no real growth between steps.
    assert (diffs <= 1e-9).all(), (
        f"propellant mass increased between steps; max delta={diffs.max():.3e}"
    )
    assert m_prop[-1] <= m_prop[0]


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    peak_pressure = float(np.max(state.P_0))
    peak_thrust = float(np.max(state.thrust))
    # Hobbyist-to-experimental solid motors should peak between roughly 1 MPa
    # and 30 MPa chamber pressure, producing thrust in the 100 N to 100 kN range.
    assert 1.0e6 < peak_pressure < 30.0e6, (
        f"peak chamber pressure {peak_pressure:.2e} Pa outside [1e6, 3e7]"
    )
    assert 100.0 < peak_thrust < 1.0e5, (
        f"peak thrust {peak_thrust:.2e} N outside [100, 1e5]"
    )
    assert state.total_impulse > 0
    assert state.specific_impulse > 0


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
            "burn_area",
            "burn_rate",
            "web",
            "V_0",
            "m_prop",
            "eta_div",
            "eta_kin",
            "eta_bl",
            "eta_2p",
            "nozzle_efficiency",
            "overall_efficiency",
        ),
    )
