"""Base adapter classes for RocketPy motor integration."""

import abc
import typing

if typing.TYPE_CHECKING:
    import rocketpy.motors as rocketpy_motors

    import machwave.states.internal_ballistics as ib_states


class RocketPyAdapterError(Exception):
    """Base exception for RocketPy adapter errors."""

    pass


M = typing.TypeVar("M", bound=ib_states.MotorState)
R = typing.TypeVar("R", bound=rocketpy_motors.Motor)


class RocketPyMotorAdapter(abc.ABC, typing.Generic[M, R]):
    """Abstract base class for RocketPy motor adapters.

    Args:
        motor_state: MotorState from internal ballistics simulation.
    """

    def __init__(self, motor_state: M) -> None:
        self.motor_state = motor_state
        self.motor = motor_state.motor
