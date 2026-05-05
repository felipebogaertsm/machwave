"""End-to-end integration tests for SolidMotor internal ballistics simulations.

The motor configurations below mirror the ones in the example scripts under
examples/ (apcp_motor, kappa_rnakka, nero_motor) but are duplicated here so
the tests stay independent of the example layer. The olympus example is not
included because it currently fails on a stale BatesSegment(spacing=...) call
that is not this test's concern.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pytest

from machwave.models import grain as grain_models
from machwave.models import motors
from machwave.models import thrust_chamber as thrust_chamber_models
from machwave.models.grain import geometries as grain_geometries
from machwave.models.propellants.formulations import solid as solid_propellants
from machwave.simulation import InternalBallisticsSimulationParams
from machwave.states import SolidMotorState
from tests.test_simulations.conftest import (
    SimulationResult,
    assert_recorded_arrays_aligned,
    run_simulation,
)


def _build_apcp_motor() -> tuple[motors.SolidMotor, InternalBallisticsSimulationParams]:
    """MIT Cherry Limeade APCP motor with five identical BATES segments."""
    propellant = solid_propellants.MIT_CHERRY_LIMEADE

    grain = grain_models.Grain(spacing=0.01)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=0.035,
        length=0.150,
    )
    for _ in range(5):
        grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=0.080,
        throat_diameter=0.022,
        divergent_angle=12,
        convergent_angle=45,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=95.25e-3,
        casing_outer_diameter=101.6e-3,
        thermal_liner_thickness=3e-3,
        internal_length=grain.total_length + 0.01,
    )
    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=6.0,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.35, 0.0, 0.0),
    )
    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )
    params = InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
        other_losses=0.12,
    )
    return motor, params


def _build_kappa_rnakka_motor() -> tuple[
    motors.SolidMotor, InternalBallisticsSimulationParams
]:
    """Richard Nakka's Kappa motor (KNDX, four BATES segments)."""
    propellant = solid_propellants.KNDX

    grain = grain_models.Grain(spacing=5e-3)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=55e-3,
        core_diameter=19e-3,
        length=101.6e-3,
    )
    for _ in range(4):
        grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=40e-3,
        throat_diameter=12.8e-3,
        divergent_angle=12,
        convergent_angle=25,
        expansion_ratio=11,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=60e-3,
        casing_outer_diameter=64e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 5e-3,
    )
    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.035, 0.0, 0.0),
    )
    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )
    params = InternalBallisticsSimulationParams(
        d_t=0.001,
        igniter_pressure=1e6,
        external_pressure=1e5,
        other_losses=0.12,
    )
    return motor, params


def _build_nero_motor() -> tuple[motors.SolidMotor, InternalBallisticsSimulationParams]:
    """Supernova Rocketry Nero motor (KNDX, four BATES segments)."""
    propellant = solid_propellants.KNDX

    grain = grain_models.Grain(spacing=10e-3)
    bates_segment = grain_geometries.BatesSegment(
        outer_diameter=41e-3,
        core_diameter=15e-3,
        length=67.5e-3,
    )
    for _ in range(4):
        grain.add_segment(bates_segment)

    nozzle = thrust_chamber_models.Nozzle(
        inlet_diameter=43e-3,
        throat_diameter=9.5e-3,
        divergent_angle=12,
        convergent_angle=40,
        expansion_ratio=8,
    )
    combustion_chamber = thrust_chamber_models.CombustionChamber(
        casing_inner_diameter=44.5e-3,
        casing_outer_diameter=50.8e-3,
        thermal_liner_thickness=1e-3,
        internal_length=grain.total_length + 10e-3,
    )
    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        dry_mass=0.85,
        nozzle=nozzle,
        combustion_chamber=combustion_chamber,
        nozzle_exit_to_grain_port_distance=0.01,
        center_of_gravity_coordinate=(0.04, 0.0, 0.0),
    )
    motor = motors.SolidMotor(
        grain=grain, propellant=propellant, thrust_chamber=thrust_chamber
    )
    params = InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1e5,
        other_losses=0.12,
    )
    return motor, params


SolidMotorBuilder = Callable[
    [], tuple[motors.SolidMotor, InternalBallisticsSimulationParams]
]


SOLID_MOTOR_BUILDERS: tuple[SolidMotorBuilder, ...] = (
    _build_apcp_motor,
    _build_kappa_rnakka_motor,
    _build_nero_motor,
)


@pytest.fixture(
    scope="module",
    params=SOLID_MOTOR_BUILDERS,
    ids=lambda builder: builder.__name__.removeprefix("_build_"),
)
def simulation_result(request: pytest.FixtureRequest) -> SimulationResult:
    motor, params = request.param()
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
    propellant_mass = np.asarray(simulation_result.state.propellant_mass)
    diffs = np.diff(propellant_mass)
    # Allow tiny floating-point noise but no real growth between steps.
    assert (diffs <= 1e-9).all(), (
        f"propellant mass increased between steps; max delta={diffs.max():.3e}"
    )
    assert propellant_mass[-1] <= propellant_mass[0]


def test_chamber_pressure_and_thrust_are_physically_plausible(
    simulation_result: SimulationResult,
) -> None:
    state = simulation_result.state
    peak_pressure = float(np.max(state.chamber_pressure))
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
            "chamber_pressure",
            "exit_pressure",
            "thrust",
            "thrust_coefficient",
            "thrust_coefficient_ideal",
            "burn_area",
            "burn_rate",
            "web",
            "free_chamber_volume",
            "propellant_mass",
            "divergent_loss",
            "kinetics_loss",
            "boundary_layer_loss",
            "two_phase_loss",
            "nozzle_efficiency",
            "overall_efficiency",
        ),
    )
