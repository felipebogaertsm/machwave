"""Tests for the RocketPy GenericMotor adapter."""

import dataclasses
from types import SimpleNamespace

import numpy as np
import pytest
import rocketpy

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.common.mass_properties as mass_properties
import machwave.models.grain as grain_models
import machwave.models.motors as motors_models
import machwave.models.propellants.formulations.solid as solid_propellants
import machwave.models.thrust_chamber as thrust_chamber_models
import machwave.simulation as machwave_simulation
from tests.factories import (
    BiliquidEngineFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
    StackedTankPressureFedFeedSystemFactory,
    TankFactory,
    TankPlacementFactory,
)
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import run_simulation

RAIL_LENGTH = 5.2


def _bates_segment(core_diameter: float = 0.035) -> grain_models.GrainSegment:
    return grain_models.geometries.BatesSegment(
        outer_diameter=0.085,
        core_diameter=core_diameter,
        length=0.150,
    )


def _star_segment() -> grain_models.GrainSegment:
    return grain_models.geometries.StarGrainSegment(
        outer_diameter=0.085,
        length=0.150,
        number_of_points=5,
        point_length=0.03,
        point_width=0.01,
    )


def _build_motor(
    segments: list[grain_models.GrainSegment],
    dry_center_of_gravity: float = 0.35,
) -> motors_models.SolidMotor:
    grain = grain_models.Grain(spacing=0.01)
    for segment in segments:
        grain.add_segment(segment)

    thrust_chamber = thrust_chamber_models.SolidMotorThrustChamber(
        nozzle=thrust_chamber_models.Nozzle(
            throat_diameter=0.022,
            divergent_angle=12,
            expansion_ratio=8,
        ),
        combustion_chamber=thrust_chamber_models.CombustionChamber(
            inner_diameter=89.25e-3,
            internal_length=grain.total_length + 0.01,
        ),
        nozzle_exit_to_grain_port_distance=0.01,
        dry_mass_properties=mass_properties.DryMassProperties(
            dry_mass=6.0,
            center_of_gravity_coordinate=(dry_center_of_gravity, 0.0, 0.0),
            moment_of_inertia=(0.19, 0.19, 0.008),
        ),
    )
    return motors_models.SolidMotor(
        grain=grain,
        propellant=solid_propellants.KNSB_NAKKA,
        thrust_chamber=thrust_chamber,
    )


def _simulate(motor: motors_models.SolidMotor) -> machwave_simulation.SimulationResult:
    params = machwave_simulation.InternalBallisticsSimulationParams(
        d_t=0.01,
        igniter_pressure=1e6,
        external_pressure=1.013e5,
    )
    return run_simulation(motor, params)


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
    motor = _build_motor([_bates_segment()] * 4, dry_center_of_gravity)
    result = _simulate(motor)
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
    motor = _build_motor([_bates_segment()] * 4, dry_center_of_gravity=0.0)
    adapter = rocketpy_adapters.RocketPyGenericMotorAdapter(
        motor=motor, simulation_result=_simulate(motor)
    )

    assert adapter.center_of_dry_mass_position == 0.0


@pytest.mark.parametrize(
    "segments",
    [
        [_star_segment()] * 4,
        [_bates_segment(core_diameter=0.035), _bates_segment(core_diameter=0.045)],
    ],
    ids=["star", "mismatched_bates"],
)
def test_grains_unsupported_by_solid_motor_fly(segments) -> None:
    motor = _build_motor(segments)
    result = _simulate(motor)
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
    result = run_simulation(motor, dataclasses.replace(params, d_t=2e-4))
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
