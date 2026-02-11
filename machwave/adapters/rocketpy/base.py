"""Base adapter classes for RocketPy motor integration."""

import abc
import typing

from machwave.core.solvers import interpolation

if typing.TYPE_CHECKING:
    import rocketpy.motors as rocketpy_motors

    import machwave.states.internal_ballistics as ib_states


class RocketPyAdapterError(Exception):
    """Base exception for RocketPy adapter errors."""

    pass


M = typing.TypeVar("M", bound=ib_states.MotorState)  # Machwave motor state
R = typing.TypeVar("R", bound=rocketpy_motors.Motor)  # RocketPy motor


class RocketPyMotorAdapter(abc.ABC, typing.Generic[M, R]):
    """Abstract base class for RocketPy motor adapters."""

    def __init__(self, motor_state: M) -> None:
        """Initialize the adapter with a Machwave motor state.

        Args:
            motor_state: The Machwave motor state to adapt.
        """
        self.motor_state = motor_state
        self.motor = motor_state.motor

    def _get_time_series(self) -> dict[str, typing.Any]:
        """Extract time series data from motor state."""
        time = self.motor_state.t
        thrust = self.motor_state.thrust

        def thrust_interpolation(new_time: float) -> float:
            return interpolation.interpolate_with_time(time, thrust, new_time)  # type: ignore

        return {
            "thrust": thrust_interpolation,
            "propellant_mass": self.motor_state.m_prop,
            # TODO: add other time series
        }

    def _get_motor_attributes(self) -> dict[str, typing.Any]:
        """Extract motor attributes from motor model class."""
        return {
            "initial_mass": self.motor.get_launch_mass(),
            "dry_mass": self.motor.get_dry_mass(),
            # TODO: add all base class attributes
        }

    @abc.abstractmethod
    def to_rocketpy_motor(self) -> R:
        """Convert the machwave motor state to a RocketPy motor object."""
        ...
