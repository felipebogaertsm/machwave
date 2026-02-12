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

    def _get_state_attributes(self) -> dict[str, typing.Any]:
        """Extract data from the motor state, output of the simulation."""
        time = self.motor_state.t
        thrust = self.motor_state.thrust

        def thrust_interpolation(new_time: float) -> float:
            return interpolation.interpolate_with_time(time, thrust, new_time)  # type: ignore

        return {
            "total_mass": ...,
            "propellant_mass": self.motor_state.m_prop,
            "center_of_mass": ...,
            "center_of_propellant_mass": ...,
            # TODO: add moment of inertia functions
            "thrust": thrust_interpolation,
            "vacuum_thrust": ...,
            "total_impulse": ...,
            "max_thrust": ...,
            "max_thrust_time": ...,
            "average_thrust": ...,
            "burn_time": ...,
            "burn_start_time": ...,
            "burn_out_time": ...,
            "burn_duration": ...,
            "exhaust_velocity": ...,
            "interpolate": INTERPOLATION_METHOD,
            "reference_pressure": ...,
        }

    def _get_motor_attributes(self) -> dict[str, typing.Any]:
        """Extract motor attributes from motor model class."""
        nozzle_outlet_diameter = self.motor.thrust_chamber.nozzle.outlet_diameter

        return {
            "coordinate_system": ROCKETPY_MOTOR_COORDINATE_SYSTEM,
            "nozzle_radius": nozzle_outlet_diameter / 2,
            "nozzle_area": geometric.get_circle_area(nozzle_outlet_diameter),
            "nozzle_position": (0, 0, 0),  # at origin in RocketPy coordinate system
            "dry_mass": self.motor.get_dry_mass(),
            "propellant_initial_mass": self.motor.initial_propellant_mass,
            "propellant_mass": ...,
            "structural_mass_ratio": ...,
            "total_mass_flow_rate": ...,
        }

    @abc.abstractmethod
    def to_rocketpy_motor(self) -> R:
        """Convert the machwave motor state to a RocketPy motor object."""
        ...
