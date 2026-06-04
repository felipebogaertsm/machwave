"""
End-to-end integration tests for SolidMotor internal ballistics simulations.

The motor configurations live in tests/test_simulations/motor_builders.py so
they can be reused by benchmarks under tests/benchmarks/.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pytest

import machwave.models.motors as motors_models
import machwave.simulation as machwave_simulation
import machwave.simulation.solid as solid_simulation
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import (
    assert_recorded_arrays_aligned,
    run_simulation,
)

SolidMotorBuilder = Callable[
    [],
    tuple[
        motors_models.SolidMotor, machwave_simulation.InternalBallisticsSimulationParams
    ],
]


SOLID_MOTOR_BUILDERS: tuple[SolidMotorBuilder, ...] = (
    motor_builders.build_apcp_motor,
    motor_builders.build_kappa_rnakka_motor,
    motor_builders.build_nero_motor,
)


@pytest.fixture(
    scope="module",
    params=SOLID_MOTOR_BUILDERS,
    ids=lambda builder: builder.__name__.removeprefix("build_"),
)
def simulation_result(
    request: pytest.FixtureRequest,
) -> solid_simulation.SolidSimulationResult:
    motor, params = request.param()
    return run_simulation(motor, params)


def test_simulation_completes_with_terminal_state(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    assert isinstance(simulation_result, solid_simulation.SolidSimulationResult)
    assert simulation_result.end_thrust is True
    assert simulation_result.end_burn is True
    assert simulation_result.time.size > 1


def test_burn_time_and_thrust_time_are_finite_and_ordered(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    assert np.isfinite(simulation_result.burn_time)
    assert np.isfinite(simulation_result.thrust_time)
    assert simulation_result.burn_time > 0.0
    assert simulation_result.thrust_time > 0.0
    # Thrust persists at least until the burn ends, then decays once the
    # nozzle becomes unchoked.
    assert simulation_result.thrust_time >= simulation_result.burn_time


def test_propellant_mass_is_monotone_non_increasing(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    propellant_mass = simulation_result.propellant_mass
    diffs = np.diff(propellant_mass)
    # Allow tiny floating-point noise but no real growth between steps.
    assert (diffs <= 1e-9).all(), (
        f"propellant mass increased between steps; max delta={diffs.max():.3e}"
    )
    assert propellant_mass[-1] <= propellant_mass[0]


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    peak_pressure = float(np.max(simulation_result.chamber_pressure))
    peak_thrust = float(np.max(simulation_result.thrust))
    # Hobbyist-to-experimental solid motors should peak between roughly 1 MPa
    # and 30 MPa chamber pressure, producing thrust in the 100 N to 100 kN range.
    assert 1.0e6 < peak_pressure < 30.0e6, (
        f"peak chamber pressure {peak_pressure:.2e} Pa outside [1e6, 3e7]"
    )
    assert 100.0 < peak_thrust < 1.0e5, (
        f"peak thrust {peak_thrust:.2e} N outside [100, 1e5]"
    )
    assert simulation_result.total_impulse > 0
    assert simulation_result.specific_impulse > 0


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    assert_recorded_arrays_aligned(simulation_result)


def test_effective_flame_temperature_uses_motor_combustion_efficiency() -> None:
    """The solid read site sources combustion efficiency from the motor.

    The effective flame temperature scales with the motor's combustion
    efficiency, so a more efficient motor produces a higher chamber pressure
    after one identical time step.
    """

    def first_step_chamber_pressure(combustion_efficiency: float) -> float:
        motor, params = motor_builders.build_nero_motor()
        motor.combustion_efficiency = combustion_efficiency
        state = solid_simulation.SolidMotorState(
            motor=motor,
            igniter_pressure=params.igniter_pressure,
            external_pressure=params.external_pressure,
            other_losses=params.other_losses,
        )
        state.run_timestep(d_t=params.d_t, external_pressure=params.external_pressure)
        return state.chamber_pressure[-1]

    assert first_step_chamber_pressure(1.0) > first_step_chamber_pressure(0.5)
