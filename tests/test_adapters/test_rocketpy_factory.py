"""Tests for choosing the RocketPy motor class from the motor."""

import pytest

import machwave.adapters.rocketpy as rocketpy_adapters
import machwave.models.grain as grain_models
import machwave.simulation.solid.results as solid_results
from tests.factories import (
    BatesSegmentFactory,
    SolidMotorFactory,
    StarGrainSegmentFactory,
)
from tests.test_simulations import motor_builders
from tests.test_simulations.conftest import run_simulation


@pytest.fixture(scope="module")
def simulation_result() -> solid_results.SolidSimulationResult:
    # The adapter class depends on the motor alone, so every case reuses this one
    # result instead of simulating each motor.
    motor, params = motor_builders.build_rocketpy_example_motor()
    return run_simulation(motor, params)


@pytest.mark.parametrize(
    ("segments", "adapter_class"),
    [
        (None, rocketpy_adapters.RocketPySolidMotorAdapter),
        (
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
            rocketpy_adapters.RocketPyGenericMotorAdapter,
        ),
        (
            [
                BatesSegmentFactory.build(
                    outer_diameter=0.085, core_diameter=0.035, length=0.150
                ),
                BatesSegmentFactory.build(
                    outer_diameter=0.085, core_diameter=0.045, length=0.150
                ),
            ],
            rocketpy_adapters.RocketPyGenericMotorAdapter,
        ),
    ],
    ids=["identical_bates", "star", "mismatched_bates"],
)
def test_create_rocketpy_motor_picks_the_adapter_for_the_grain(
    segments, adapter_class, simulation_result
) -> None:
    motor, _ = motor_builders.build_rocketpy_example_motor(segments=segments)

    rocketpy_motor = rocketpy_adapters.create_rocketpy_motor(
        motor=motor, simulation_result=simulation_result
    )

    assert type(rocketpy_motor) is adapter_class


def test_create_rocketpy_motor_adapts_a_biliquid_engine_as_a_generic_motor(
    simulation_result,
) -> None:
    engine, _ = motor_builders.build_1kn_biliquid_engine()

    rocketpy_motor = rocketpy_adapters.create_rocketpy_motor(
        motor=engine, simulation_result=simulation_result
    )

    assert type(rocketpy_motor) is rocketpy_adapters.RocketPyGenericMotorAdapter


def test_create_rocketpy_motor_rejects_an_empty_grain(simulation_result) -> None:
    motor = SolidMotorFactory.build(grain=grain_models.Grain())

    with pytest.raises(ValueError, match="Grain must have at least one segment"):
        rocketpy_adapters.create_rocketpy_motor(
            motor=motor, simulation_result=simulation_result
        )
