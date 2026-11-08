"""Tests for the RocketPy GenericMotor adapter."""

from types import SimpleNamespace

import numpy as np
import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
from tests.factories import (
    BatesSegmentFactory,
    BiliquidEngineFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
    StackedTankPressureFedFeedSystemFactory,
    StarGrainSegmentFactory,
    TankFactory,
    TankPlacementFactory,
)
from tests.test_simulations.conftest import run_simulation
from tests.test_simulations import motor_builders

RAIL_LENGTH = 5.2
# Absolute because the center of mass reaches the nozzle exit at burnout when the
# dry center of gravity sits there. SolidMotor takes the propellant mass from its
# own grain regression and GenericMotor from thrust over a constant exhaust
# velocity; the two differ by about 1e-5 of the motor mass, which moves the center
# of mass by less than 3e-7 m at the sampled times.
CENTER_OF_MASS_TOLERANCE = 1e-6


def _build_adapter_without_init(motor) -> rocketpy_adapters.RocketPyGenericMotorAdapter:
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter.__new__(
        rocketpy_adapters.RocketPyGenericMotorAdapter
    )
    adapter.motor = motor
    adapter.simulation_result = SimpleNamespace(
        time=np.array([0.0, 1.0]),
        thrust=np.array([100.0, 100.0]),
        thrust_time=1.0,
        exit_pressure=np.array([1e5, 1e5]),
        initial_propellant_mass=2.5,
    )
    return adapter


def _fly(adapter: rocketpy_adapters.RocketPyGenericMotorAdapter) -> rocketpy.Flight:
    flight = _fly(adapter)

    assert adapter.propellant_initial_mass == pytest.approx(
        result.initial_propellant_mass
    )
    assert flight.z(flight.t_final) > RAIL_LENGTH


def test_biliquid_engine_flies() -> None:
    motor, params = motor_builders.build_1kn_biliquid_engine()
    result = run_simulation(motor, params)
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=result
    )

    flight = _fly(adapter)

    dry_mass_properties = motor.thrust_chamber.dry_mass_properties
    assert dry_mass_properties is not None
    dry_mass = dry_mass_properties.dry_mass
    propellant_mass = result.initial_propellant_mass
    assert adapter.center_of_mass(0.0) == pytest.approx(
        (
            dry_mass * dry_mass_properties.center_of_gravity_coordinate[0]
            + propellant_mass * result.propellant_cog[0, 0]
        )
        / (dry_mass + propellant_mass)
    )
    assert flight.z(flight.t_final) > RAIL_LENGTH
