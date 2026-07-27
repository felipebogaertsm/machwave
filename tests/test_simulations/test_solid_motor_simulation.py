"""
End-to-end integration tests for SolidMotor internal ballistics simulations.

The motor configurations live in tests/test_simulations/motor_builders.py so
they can be reused by benchmarks under tests/benchmarks/.
"""

from __future__ import annotations

import dataclasses
import io
from typing import Callable

import numpy as np
import pytest

import machwave.core.compressible_flow.isentropic as isentropic
import machwave.models.motors as motors_models
import machwave.models.nozzle_losses as nozzle_losses
import machwave.models.nozzle_losses.components.constant as constant
import machwave.models.nozzle_losses.components.spp1975 as spp1975
import machwave.models.propellants as propellants
import machwave.simulation as machwave_simulation
import machwave.simulation.solid as solid_simulation
import machwave.simulation.states as simulation_states
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
    # Flow separation bounds the overexpanded pressure-thrust term, so thrust
    # stays non-negative through tail-off.
    min_thrust = float(np.min(simulation_result.thrust))
    assert min_thrust >= 0.0, f"thrust dips negative: {min_thrust:.2e} N"
    assert simulation_result.total_impulse > 0
    assert simulation_result.specific_impulse > 0


def test_recorded_per_timestep_arrays_are_aligned(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    assert_recorded_arrays_aligned(simulation_result)


def test_exit_pressure_is_finite_and_positive(
    simulation_result: solid_simulation.SolidSimulationResult,
) -> None:
    assert np.all(np.isfinite(simulation_result.exit_pressure))
    assert np.all(simulation_result.exit_pressure > 0.0)


def test_thrust_equals_thrust_coefficient_times_chamber_pressure_times_throat_area():
    motor, params = motor_builders.build_nero_motor()
    result = run_simulation(motor, params)
    throat_area = motor.thrust_chamber.nozzle.get_throat_area()
    np.testing.assert_allclose(
        result.thrust,
        result.thrust_coefficient * result.chamber_pressure * throat_area,
        rtol=1e-9,
    )


def test_loss_fraction_series_match_model_components() -> None:
    """The result exposes one named, in-range loss series per model component."""
    motor, params = motor_builders.build_nero_motor()
    result = run_simulation(motor, params)

    component_names = set(motor.nozzle_loss_model.component_names)
    assert set(result.loss_fractions) == component_names
    assert result.loss_labels == motor.nozzle_loss_model.component_labels
    for series in result.loss_fractions.values():
        assert np.all(np.isfinite(series))
        assert np.all((series >= 0.0) & (series <= 1.0))


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
        )
        state.run_timestep(d_t=params.d_t, external_pressure=params.external_pressure)
        return state.chamber_pressure[-1]

    assert first_step_chamber_pressure(1.0) > first_step_chamber_pressure(0.5)


def test_report_includes_nozzle_losses() -> None:
    """The printed report includes the nozzle efficiency and every loss label."""
    motor, params = motor_builders.build_nero_motor()
    result = run_simulation(motor, params)

    buffer = io.StringIO()
    result.report(file=buffer)
    output = buffer.getvalue()

    assert "Average nozzle efficiency" in output
    for label in motor.nozzle_loss_model.component_labels.values():
        assert label in output


def test_all_both_targets_match_legacy_scalar_correction() -> None:
    """With every loss on both thrust coefficient terms, the per-term model
    reduces to the legacy ideal C_F times the nozzle efficiency.

    This guards the boundary-layer and two-phase numerics (which read the
    geometric expansion ratio) and the composition math against the previous
    single-scalar correction.
    """
    motor, params = motor_builders.build_nero_motor()
    motor.nozzle_loss_model = nozzle_losses.NozzleLossModel(
        [
            spp1975.KineticsLoss(),
            spp1975.BoundaryLayerLoss(),
            spp1975.TwoPhaseFlowLoss(),
            constant.ConstantFractionLoss(0.12, name="other_losses"),
        ],
        mixture_type=propellants.MixtureType.SOLID,
    )
    result = run_simulation(motor, params)

    np.testing.assert_allclose(
        result.thrust_coefficient,
        result.ideal_thrust_coefficient * result.nozzle_efficiency,
        rtol=1e-12,
    )


def test_vacuum_run_terminates_on_tail_off() -> None:
    """Against zero ambient pressure the nozzle stays choked, so tail-off ends it."""
    motor, params = motor_builders.build_nero_motor()
    result = run_simulation(motor, dataclasses.replace(params, external_pressure=0.0))

    assert result.end_thrust is True
    assert result.end_burn is True
    assert result.thrust_time > result.burn_time
    peak_thrust = float(np.max(result.thrust))
    assert result.thrust[-1] < simulation_states.TAIL_OFF_THRUST_FRACTION * peak_thrust


def test_sea_level_run_still_ends_on_loss_of_choking() -> None:
    """Tail-off sits far below the un-choking pressure, so it never preempts it."""
    motor, params = motor_builders.build_nero_motor()
    result = run_simulation(motor, params)

    propellant_properties = motor.propellant.properties
    assert propellant_properties is not None
    assert not isentropic.is_flow_choked(
        float(result.chamber_pressure[-1]),
        params.external_pressure,
        isentropic.get_critical_pressure_ratio(propellant_properties.k_chamber),
    )
    peak_thrust = float(np.max(result.thrust))
    assert result.thrust[-1] > simulation_states.TAIL_OFF_THRUST_FRACTION * peak_thrust


def test_moment_of_inertia_is_guarded_past_burnout() -> None:
    """Past burnout the loop records a zero inertia tensor instead of crashing.

    A 3D grain raises past its web thickness, and the simulation keeps advancing
    the web after burnout until the flow un-chokes. The loop must skip the mass
    property queries once the propellant is gone, mirroring the center-of-gravity
    guard, rather than querying the grain out of range.
    """
    motor, params = motor_builders.build_finocyl_motor()
    state = solid_simulation.SolidMotorState(
        motor=motor,
        igniter_pressure=params.igniter_pressure,
        external_pressure=params.external_pressure,
    )
    # Fully consumed: volume and mass are zero, and a direct moment-of-inertia
    # query at this web would raise GrainGeometryError.
    state.web = [motor.grain.segments[0].get_web_thickness() * 1.5]

    # Small step so the one-shot chamber-pressure update stays well-behaved; the
    # mass-property guard runs regardless of the step size.
    state.run_timestep(d_t=1e-5, external_pressure=params.external_pressure)

    np.testing.assert_array_equal(state.propellant_moi[-1], np.zeros((3, 3)))
    assert np.all(np.isnan(state.propellant_cog[-1]))
