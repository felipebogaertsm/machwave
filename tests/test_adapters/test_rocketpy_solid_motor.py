"""Tests for the RocketPy SolidMotor adapter."""

from types import SimpleNamespace

import numpy as np
import pytest

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.models.grain as grain_models

from tests.factories import (
    BatesSegmentFactory,
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

    with pytest.raises(ValueError, match="requires dry mass properties"):
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


@pytest.mark.parametrize("offset", [0.0, 0.01, 0.25])
def test_grain_center_of_mass_is_measured_from_the_nozzle_exit(offset) -> None:
    thrust_chamber = SolidMotorThrustChamberFactory.build(
        nozzle_exit_to_grain_port_distance=offset
    )
    motor = SolidMotorFactory.build(thrust_chamber=thrust_chamber)
    adapter = _build_adapter_without_init(motor)

    attrs = adapter._get_rocketpy_attributes()

    assert attrs["grains_center_of_mass_position"] == pytest.approx(
        motor.grain.get_center_of_gravity(web_distance=0.0)[0] + offset
    )


def _build_adapter_with_inertia(
    motor, tensors
) -> rocketpy_adapters.RocketPySolidMotorAdapter:
    """Return an adapter whose stub result carries the given inertia tensors."""
    adapter = _build_adapter_without_init(motor)
    adapter.simulation_result.propellant_moi = np.asarray(tensors)
    return adapter


def test_propellant_inertia_maps_the_axial_moment_to_e3() -> None:
    grain = grain_models.Grain()
    for _ in range(4):
        grain.add_segment(BatesSegmentFactory.build())
    motor = SolidMotorFactory.build(grain=grain)
    tensor = grain.get_moment_of_inertia(ideal_density=1800.0, web_distance=0.0)
    adapter = _build_adapter_with_inertia(motor, [tensor, tensor])

    I_11 = adapter.propellant_I_11(0.0)
    I_22 = adapter.propellant_I_22(0.0)
    I_33 = adapter.propellant_I_33(0.0)

    assert I_33 == pytest.approx(tensor[0, 0])
    assert I_11 == pytest.approx(I_22)
    assert I_33 < I_11


def test_propellant_inertia_off_diagonal_terms_follow_the_axis_permutation() -> None:
    # machwave axes (x axial, y, z) map onto RocketPy axes (e_3, e_1, e_2)
    tensor = np.array(
        [
            [1.0, 4.0, 5.0],
            [4.0, 2.0, 6.0],
            [5.0, 6.0, 3.0],
        ]
    )
    adapter = _build_adapter_with_inertia(SolidMotorFactory.build(), [tensor, tensor])

    assert adapter.propellant_I_11(0.0) == pytest.approx(2.0)
    assert adapter.propellant_I_22(0.0) == pytest.approx(3.0)
    assert adapter.propellant_I_33(0.0) == pytest.approx(1.0)
    assert adapter.propellant_I_12(0.0) == pytest.approx(6.0)
    assert adapter.propellant_I_13(0.0) == pytest.approx(4.0)
    assert adapter.propellant_I_23(0.0) == pytest.approx(5.0)
