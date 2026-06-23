"""Tests for the RocketPy SolidMotor adapter."""

from types import SimpleNamespace

import numpy as np
import pytest

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.models.grain as grain_models

from tests.factories import (
    ConicalGrainSegmentFactory,
    DGrainSegmentFactory,
    MultiPortGrainSegmentFactory,
    RodAndTubeGrainSegmentFactory,
    SolidMotorFactory,
    SolidMotorThrustChamberFactory,
    StarGrainSegmentFactory,
    WagonWheelGrainSegmentFactory,
)


def _stub_simulation_result() -> SimpleNamespace:
    """Return a stand-in result with the fields read by the base adapter."""
    time = np.array([0.0, 1.0])
    thrust = np.array([100.0, 100.0])
    return SimpleNamespace(
        time=time,
        thrust=thrust,
        thrust_time=1.0,
        exit_pressure=np.array([1e5, 1e5]),
    )


def _build_adapter_without_init(motor) -> rocketpy_adapters.RocketPySolidMotorAdapter:
    """Bypass __init__ so the test isolates the geometry validation."""
    adapter = rocketpy_adapters.RocketPySolidMotorAdapter.__new__(
        rocketpy_adapters.RocketPySolidMotorAdapter
    )
    adapter.motor = motor
    adapter.simulation_result = _stub_simulation_result()
    return adapter


@pytest.mark.parametrize(
    "segment_factory",
    [
        StarGrainSegmentFactory,
        WagonWheelGrainSegmentFactory,
        ConicalGrainSegmentFactory,
        DGrainSegmentFactory,
        MultiPortGrainSegmentFactory,
        RodAndTubeGrainSegmentFactory,
    ],
)
def test_non_bates_geometry_raises_value_error(segment_factory) -> None:
    grain = grain_models.Grain()
    grain.add_segment(segment_factory.build())
    motor = SolidMotorFactory.build(grain=grain)
    adapter = _build_adapter_without_init(motor)

    with pytest.raises(ValueError, match="only supports BATES grain geometry"):
        adapter._get_rocketpy_attributes()


def test_bates_geometry_produces_expected_keys() -> None:
    motor = SolidMotorFactory.build()
    adapter = _build_adapter_without_init(motor)

    attrs = adapter._get_rocketpy_attributes()

    assert attrs["grain_number"] == motor.grain.segment_count
    assert attrs["grain_outer_radius"] == pytest.approx(
        motor.grain.segments[0].outer_diameter / 2
    )
    assert attrs["grain_initial_inner_radius"] == pytest.approx(
        motor.grain.segments[0].core_diameter / 2
    )
    assert attrs["grain_initial_height"] == pytest.approx(
        motor.grain.segments[0].length
    )
    assert attrs["throat_radius"] == pytest.approx(
        motor.thrust_chamber.nozzle.throat_diameter / 2
    )


def test_missing_dry_mass_properties_raises_value_error() -> None:
    thrust_chamber = SolidMotorThrustChamberFactory.build(dry_mass_properties=None)
    motor = SolidMotorFactory.build(thrust_chamber=thrust_chamber)
    adapter = _build_adapter_without_init(motor)

    with pytest.raises(ValueError, match="Dry mass properties are not defined"):
        adapter._get_rocketpy_attributes()


def test_dry_mass_properties_are_forwarded() -> None:
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        dry_mass=1.5,
        center_of_gravity_coordinate=(0.2, 0.0, 0.0),
        moment_of_inertia=(0.12, 0.12, 0.03),
    )
    motor = SolidMotorFactory.build(thrust_chamber=thrust_chamber)
    adapter = _build_adapter_without_init(motor)

    attrs = adapter._get_rocketpy_attributes()

    assert attrs["dry_mass"] == pytest.approx(1.5)
    assert attrs["center_of_dry_mass_position"] == pytest.approx(0.2)
    assert attrs["dry_inertia"] == pytest.approx((0.12, 0.12, 0.03))
