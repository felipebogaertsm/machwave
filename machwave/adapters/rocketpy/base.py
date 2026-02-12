"""Base adapter classes for RocketPy motor integration."""

import abc
import typing

from machwave.core.solvers import interpolation
from machwave.core import geometric

if typing.TYPE_CHECKING:
    import rocketpy.motors as rocketpy_motors

    import machwave.states.internal_ballistics as ib_states


class RocketPyAdapterError(Exception):
    """Base exception for RocketPy adapter errors."""

    pass


M = typing.TypeVar("M", bound=ib_states.MotorState)  # Machwave motor state
R = typing.TypeVar("R", bound=rocketpy_motors.Motor)  # RocketPy motor

ROCKETPY_MOTOR_COORDINATE_SYSTEM = "nozzle_to_combustion_chamber"
RESHAPE_THRUST_SOURCE = False
INTERPOLATION_METHOD = "linear"


class RocketPyMotorAdapter(abc.ABC, typing.Generic[M, R]):
    """Abstract base class for RocketPy motor adapters."""

    def __init__(self, motor_state: M) -> None:
        """Initialize the adapter with a Machwave motor state.

        Args:
            motor_state: The Machwave motor state to adapt.
        """
        self.motor_state = motor_state
        self.motor = motor_state.motor

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        """Extract data from the motor state, output of the simulation."""
        time = self.motor_state.t
        thrust = self.motor_state.thrust
        nozzle_outlet_diameter = self.motor.thrust_chamber.nozzle.outlet_diameter
        dry_mass = self.motor.thrust_chamber.get_dry_mass()

        def thrust_interpolation(new_time: float) -> float:
            return interpolation.interpolate_with_time(time, thrust, new_time)  # type: ignore

        return {
            "thrust_source": thrust_interpolation,
            "dry_inertia": ...,  # dry mass MoI at center_of_dry_mass_position
            "nozzle_radius": nozzle_outlet_diameter / 2,
            "center_of_dry_mass_position": ...,  # in RocketPy coordinate system
            "dry_mass": dry_mass,  # in kg
            "nozzle_position": ...,  # at origin in RocketPy coordinate system
            "burn_time": ...,
            "reshape_thrust_source": RESHAPE_THRUST_SOURCE,
            "interpolation_method": INTERPOLATION_METHOD,
            "coordinate_system_orientation": ROCKETPY_MOTOR_COORDINATE_SYSTEM,
            "reference_pressure": ...,
        }

    def to_rocketpy_motor(self) -> R:
        """Convert the machwave motor state to a RocketPy motor object."""
        ...
