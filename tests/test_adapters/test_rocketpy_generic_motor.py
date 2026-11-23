"""Tests for the RocketPy GenericMotor adapter."""

import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
from tests.factories import (
    BatesSegmentFactory,
    StarGrainSegmentFactory,
)
from tests.test_simulations.conftest import run_simulation
from tests.test_simulations import motor_builders

RAIL_LENGTH = 5.2
# absolute because the center of mass can reach the nozzle exit at burnout, and the
# two RocketPy classes compute the propellant mass slightly differently
CENTER_OF_MASS_TOLERANCE = 1e-6


def test_chamber_attributes_describe_the_grain_and_combustion_chamber() -> None:
    motor, params = motor_builders.build_rocketpy_example_motor()
    result = run_simulation(motor, params)
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=result
    )
    thrust_chamber = motor.thrust_chamber

    assert adapter.chamber_radius == pytest.approx(
        thrust_chamber.combustion_chamber.inner_diameter / 2
    )
    assert adapter.chamber_height == pytest.approx(motor.grain.total_length)
    assert adapter.chamber_position == pytest.approx(
        motor.grain.get_center_of_gravity(web_distance=0.0)[0]
        + thrust_chamber.nozzle_exit_to_grain_port_distance
    )
    assert adapter.propellant_initial_mass == pytest.approx(
        result.initial_propellant_mass
    )


@pytest.mark.parametrize("dry_center_of_gravity", [0.35, 0.0])
def test_bates_motor_matches_the_solid_motor_adapter(dry_center_of_gravity) -> None:
    motor, params = motor_builders.build_rocketpy_example_motor(
        dry_center_of_gravity=dry_center_of_gravity
    )
    result = run_simulation(motor, params)
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
            solid_motor.center_of_mass(time), abs=CENTER_OF_MASS_TOLERANCE
        )
        assert generic_motor.I_11(time) == pytest.approx(solid_motor.I_11(time))
        assert generic_motor.I_33(time) == pytest.approx(solid_motor.I_33(time))
        assert generic_motor.total_mass_flow_rate(time) == pytest.approx(
            solid_motor.total_mass_flow_rate(time)
        )


def test_dry_center_of_gravity_at_the_nozzle_exit_is_preserved() -> None:
    motor, params = motor_builders.build_rocketpy_example_motor(
        dry_center_of_gravity=0.0
    )
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=run_simulation(motor, params)
    )

    assert adapter.center_of_dry_mass_position == 0.0


@pytest.mark.parametrize(
    "segments",
    [
        [
            StarGrainSegmentFactory.build(
                outer_diameter=0.085,
                length=0.150,
                number_of_points=5,
                point_length=0.03,
                point_width=0.01,
            )
        ]
        * 4,
        [
            BatesSegmentFactory.build(
                outer_diameter=0.085, core_diameter=0.035, length=0.150
            ),
            BatesSegmentFactory.build(
                outer_diameter=0.085, core_diameter=0.045, length=0.150
            ),
        ],
    ],
    ids=["star", "mismatched_bates"],
)
def test_grains_unsupported_by_solid_motor_fly(segments) -> None:
    motor, params = motor_builders.build_rocketpy_example_motor(segments=segments)
    result = run_simulation(motor, params)
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
