"""RocketPy adapter for Machwave solid motors."""

import typing

from machwave.adapters.rocketpy.base import RocketPyMotorAdapter

if typing.TYPE_CHECKING:
    from machwave.states.internal_ballistics.solid_motor import SolidMotorState


class RocketPySolidMotorAdapter(RocketPyMotorAdapter["SolidMotorState"]):
    """Adapter to use Machwave SolidMotorState as a RocketPy SolidMotor."""

    _rocketpy_motor_class = "SolidMotor"
