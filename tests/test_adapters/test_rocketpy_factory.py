"""Tests for choosing the RocketPy motor class from the grain geometry."""

import pytest

import machwave.adapters.rocketpy as rocketpy_adapters
from tests.test_adapters.conftest import (
    bates_segment,
    build_motor,
    simulate,
    star_segment,
)


@pytest.mark.parametrize(
    ("segments", "adapter_class"),
    [
        ([bates_segment()] * 4, rocketpy_adapters.RocketPySolidMotorAdapter),
        ([star_segment()] * 4, rocketpy_adapters.RocketPyGenericMotorAdapter),
        (
            [bates_segment(core_diameter=0.035), bates_segment(core_diameter=0.045)],
            rocketpy_adapters.RocketPyGenericMotorAdapter,
        ),
    ],
    ids=["identical_bates", "star", "mismatched_bates"],
)
def test_create_rocketpy_motor_picks_the_adapter_for_the_grain(
    segments, adapter_class
) -> None:
    motor = build_motor(segments)

    rocketpy_motor = rocketpy_adapters.create_rocketpy_motor(
        motor=motor, simulation_result=simulate(motor)
    )

    assert type(rocketpy_motor) is adapter_class
