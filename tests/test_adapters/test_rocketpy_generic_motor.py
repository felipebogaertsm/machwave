"""Tests for the RocketPy GenericMotor adapter."""

from types import SimpleNamespace

import numpy as np
import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
from tests.factories import SolidMotorFactory, SolidMotorThrustChamberFactory
from tests.test_adapters.conftest import (
    bates_segment,
    build_motor,
    simulate,
    star_segment,
)

RAIL_LENGTH = 5.2


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


def test_chamber_attributes_describe_the_grain_and_combustion_chamber() -> None:
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle_exit_to_grain_port_distance=0.01
    )
    motor = SolidMotorFactory.build(thrust_chamber=thrust_chamber)
    adapter = _build_adapter_without_init(motor)

    attrs = adapter._get_rocketpy_attributes()

    assert attrs["chamber_radius"] == pytest.approx(
        thrust_chamber.combustion_chamber.inner_diameter / 2
    )
    assert attrs["chamber_height"] == pytest.approx(motor.grain.total_length)
    assert attrs["chamber_position"] == pytest.approx(
        motor.grain.get_center_of_gravity(web_distance=0.0)[0] + 0.01
    )
    assert attrs["propellant_initial_mass"] == pytest.approx(2.5)


@pytest.mark.parametrize("dry_center_of_gravity", [0.35, 0.0])
def test_bates_motor_matches_the_solid_motor_adapter(dry_center_of_gravity) -> None:
    motor = build_motor([bates_segment()] * 4, dry_center_of_gravity)
    result = simulate(motor)
    generic_motor = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=result
    )
    solid_motor = rocketpy_adapters.RocketPySolidMotorAdapter(
        motor=motor, simulation_result=result
    )

    for time in (0.0, 0.5, 1.0, result.thrust_time):
        assert generic_motor.total_mass(time) == pytest.approx(
            solid_motor.total_mass(time)
        )
        assert generic_motor.center_of_mass(time) == pytest.approx(
            solid_motor.center_of_mass(time), abs=1e-6
        )
        assert generic_motor.I_11(time) == pytest.approx(solid_motor.I_11(time))
        assert generic_motor.I_33(time) == pytest.approx(solid_motor.I_33(time))
        assert generic_motor.total_mass_flow_rate(time) == pytest.approx(
            solid_motor.total_mass_flow_rate(time)
        )


def test_dry_center_of_gravity_at_the_nozzle_exit_is_preserved() -> None:
    motor = build_motor([bates_segment()] * 4, dry_center_of_gravity=0.0)
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=simulate(motor)
    )

    assert adapter.center_of_dry_mass_position == 0.0


@pytest.mark.parametrize(
    "segments",
    [
        [star_segment()] * 4,
        [bates_segment(core_diameter=0.035), bates_segment(core_diameter=0.045)],
    ],
    ids=["star", "mismatched_bates"],
)
def test_grains_unsupported_by_solid_motor_fly(segments) -> None:
    motor = build_motor(segments)
    result = simulate(motor)
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=result
    )

    rocket = rocketpy.Rocket(
        radius=0.0508,
        mass=15.0,
        inertia=(6.0, 6.0, 0.035),
        power_off_drag=0.5,
        power_on_drag=0.5,
        center_of_mass_without_motor=0.0,
    )
    rocket.add_motor(adapter, position=-0.6)
    flight = rocketpy.Flight(
        rocket=rocket,
        environment=rocketpy.Environment(),
        rail_length=RAIL_LENGTH,
        inclination=85,
        heading=0,
        max_time=2.0,
    )

    assert adapter.propellant_initial_mass == pytest.approx(
        result.initial_propellant_mass
    )
    assert flight.z(flight.t_final) > RAIL_LENGTH
