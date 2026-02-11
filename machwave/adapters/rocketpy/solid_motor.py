"""Solid motor adapter for RocketPy."""

import typing

from . import base as rocketpy_base

if typing.TYPE_CHECKING:
    import rocketpy.motors as rocketpy_motors

    import machwave.states.internal_ballistics.solid_motor as solid_motor_state


class RocketPySolidMotorAdapter(
    rocketpy_base.RocketPyMotorAdapter[
        solid_motor_state.SolidMotorState, rocketpy_motors.SolidMotor
    ]
):
    """Adapter to convert machwave SolidMotorState to RocketPy SolidMotor."""
