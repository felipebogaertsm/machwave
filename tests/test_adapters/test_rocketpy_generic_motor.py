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
    rocket = rocketpy.Rocket(
        radius=0.0508,
        mass=15.0,
        inertia=(6.0, 6.0, 0.035),
        power_off_drag=0.5,
        power_on_drag=0.5,
        center_of_mass_without_motor=0.0,
    )
    rocket.add_motor(adapter, position=-0.6)
    return rocketpy.Flight(
        rocket=rocket,
        environment=rocketpy.Environment(),
        rail_length=RAIL_LENGTH,
        inclination=85,
        heading=0,
        max_time=2.0,
    )


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


def test_chamber_attributes_describe_the_envelope_of_the_tanks() -> None:
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank=TankFactory.build(fluid_name="N2O", volume=0.01),
        oxidizer_tank_placement=TankPlacementFactory.build(
            inner_diameter=0.2, nozzle_exit_to_aft_end_distance=0.6
        ),
        fuel_tank_placement=TankPlacementFactory.build(
            inner_diameter=0.16, nozzle_exit_to_aft_end_distance=0.3
        ),
    )
    adapter = _build_adapter_without_init(
        BiliquidEngineFactory.build(feed_system=feed_system)
    )

    attrs = adapter._get_rocketpy_attributes()

    oxidizer_forward_end = 0.6 + 0.01 / (np.pi * 0.1**2)
    assert attrs["chamber_radius"] == pytest.approx(0.1)
    assert attrs["chamber_height"] == pytest.approx(oxidizer_forward_end - 0.3)
    assert attrs["chamber_position"] == pytest.approx((oxidizer_forward_end + 0.3) / 2)


def test_a_tank_without_placement_raises() -> None:
    feed_system = StackedTankPressureFedFeedSystemFactory.build(
        oxidizer_tank_placement=TankPlacementFactory.build()
    )
    adapter = _build_adapter_without_init(
        BiliquidEngineFactory.build(feed_system=feed_system)
    )

    with pytest.raises(ValueError, match="tank placement.*'fuel'"):
        adapter._get_rocketpy_attributes()


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
