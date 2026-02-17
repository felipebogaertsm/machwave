"""Base adapter classes for RocketPy motor integration."""

import abc
import typing

import numpy as np
import numpy.typing as npt

if typing.TYPE_CHECKING:
    from rocketpy import Function

    import machwave.states.internal_ballistics as ib_states


class RocketPyAdapterError(Exception):
    """Base exception for RocketPy adapter errors."""

    pass


M = typing.TypeVar("M", bound="ib_states.MotorState")  # Machwave motor state

ROCKETPY_MOTOR_COORDINATE_SYSTEM = "nozzle_to_combustion_chamber"
RESHAPE_THRUST_CURVE = False
INTERPOLATION_METHOD = "linear"


class RocketPyMotorAdapter(abc.ABC, typing.Generic[M]):
    """Abstract base class for RocketPy motor adapters.

    Dynamically inherits from the appropriate RocketPy Motor class. Subclasses must
    specify _rocketpy_motor_class to indicate which RocketPy Motor class to adapt to.
    """

    # Subclasses must override this to specify the RocketPy motor class name
    _rocketpy_motor_class: typing.ClassVar[str] = "Motor"

    @staticmethod
    def _require_rocketpy() -> None:
        """Ensure rocketpy is available.

        Raises:
            ImportError: If rocketpy is not installed.
        """
        try:
            import rocketpy  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "RocketPy adapters require the 'rocketpy' package. Install it with: "
                "pip install rocketpy"
            ) from e

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        """
        Dynamically inherit from specified RocketPy Motor class when subclass is
        created.
        """
        super().__init_subclass__(**kwargs)

        cls._require_rocketpy()
        import rocketpy.motors as rocketpy_motors

        # Get the specific motor class to inherit from
        motor_class_name = cls._rocketpy_motor_class
        if not hasattr(rocketpy_motors, motor_class_name):
            raise AttributeError(
                f"RocketPy motors module has no class '{motor_class_name}'"
            )

        motor_class = getattr(rocketpy_motors, motor_class_name)

        # Dynamically add the specific Motor class to the base classes if not already there
        if not any(
            isinstance(base, type) and issubclass(base, motor_class)
            for base in cls.__bases__
        ):
            cls.__bases__ = (motor_class,) + cls.__bases__

    def __init__(self, motor_state: M) -> None:
        """Initialize the adapter with a Machwave motor state.

        Args:
            The Machwave motor state to adapt.
        """
        self._require_rocketpy()

        self.motor_state = motor_state
        self.motor = motor_state.motor

        attrs = self._get_rocketpy_attributes()
        super().__init__(**attrs)

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        """Extract motor attributes and time series compatible with RocketPy."""
        time = self.motor_state.t
        thrust = self.motor_state.thrust

        thrust_chamber = self.motor.thrust_chamber
        nozzle = thrust_chamber.nozzle

        thrust_source = np.column_stack((time, thrust))

        # Axial position of the dry mass center of gravity.
        # Both machwave and RocketPy use nozzle exit as origin, positive toward
        # the bulkhead ("nozzle_to_combustion_chamber" orientation).
        center_of_dry_mass_position = (
            thrust_chamber.center_of_gravity_coordinate[0]
            if thrust_chamber.center_of_gravity_coordinate is not None
            else 0.0
        )

        return {
            "thrust_source": thrust_source,
            "dry_inertia": ...,  # TODO: dry mass MoI at center_of_dry_mass_position
            "nozzle_radius": nozzle.outlet_diameter / 2,
            "center_of_dry_mass_position": center_of_dry_mass_position,
            "dry_mass": self.motor.get_dry_mass(),
            "nozzle_position": 0.0,
            "burn_time": (time[0], self.motor_state.thrust_time),
            "reshape_thrust_curve": RESHAPE_THRUST_CURVE,
            "interpolation_method": INTERPOLATION_METHOD,
            "coordinate_system_orientation": ROCKETPY_MOTOR_COORDINATE_SYSTEM,
            "reference_pressure": self.motor_state.P_exit[0],
        }

    @property
    def exhaust_velocity(self) -> "Function":
        """Exhaust velocity as a function of time.

        Computed as total impulse divided by propellant initial mass,
        assumed constant and discretized over the burn time.

        Returns:
            Gas exhaust velocity [m/s] as a function of time.
        """
        from rocketpy import Function

        v_exh = self.motor_state.total_impulse / self.propellant_initial_mass
        return Function(v_exh).set_discrete_based_on_model(self.thrust)

    @property
    def propellant_initial_mass(self) -> float:
        """Initial mass of propellant.

        Returns:
            Initial propellant mass [kg].
        """
        return self.motor_state.initial_propellant_mass

    @property
    def center_of_propellant_mass(self) -> "Function":
        """Position of propellant center of mass as a function of time.

        Uses pre-computed values from motor state simulation.
        Extracts the x-coordinate (axial position) from the propellant's center of
        gravity over time.

        Returns:
            Function object with (time, position) data [m].
        """
        from rocketpy import Function

        time = self.motor_state.t
        # Extract x-coordinate from stored COG values
        center_positions = np.array([cog[0] for cog in self.motor_state.propellant_cog])
        data = np.column_stack((time, center_positions))
        return Function(data)

    def _get_inertia_tensor_over_time(self) -> npt.NDArray[np.float64]:
        """Get pre-computed inertia tensors from motor state.

        Returns:
            Array of shape (n_timesteps, 3, 3) containing inertia tensors.
        """
        return np.array(self.motor_state.propellant_moi, dtype=np.float64)

    def _get_propellant_inertia_component(self, i: int, j: int) -> "Function":
        """Get a specific component of the propellant inertia tensor.

        Args:
            i: First index (0, 1, or 2).
            j: Second index (0, 1, or 2).

        Returns:
            Function object with (time, I_ij) data [kg-m^2].
        """
        from rocketpy import Function

        time = self.motor_state.t
        inertia_tensors = self._get_inertia_tensor_over_time()
        I_values = inertia_tensors[:, i, j]
        data = np.column_stack((time, I_values))
        return Function(data)

    @property
    def propellant_I_11(self) -> "Function":
        """Inertia tensor I_11 (I_xx) component of the propellant.

        Inertia relative to the e_1 axis (perpendicular to motor body axis), centered at
        the instantaneous propellant center of mass.

        Returns:
            Function object with (time, I_11) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 0)

    @property
    def propellant_I_12(self) -> "Function":
        """Inertia tensor I_12 (I_xy) component of the propellant.

        Returns:
            Function object with (time, I_12) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 1)

    @property
    def propellant_I_13(self) -> "Function":
        """Inertia tensor I_13 (I_xz) component of the propellant.

        Returns:
            Function object with (time, I_13) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 2)

    @property
    def propellant_I_22(self) -> "Function":
        """Inertia tensor I_22 (I_yy) component of the propellant.

        Inertia relative to the e_2 axis (perpendicular to motor body axis), centered at
        the instantaneous propellant center of mass.

        Returns:
            Function object with (time, I_22) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(1, 1)

    @property
    def propellant_I_23(self) -> "Function":
        """Inertia tensor I_23 (I_yz) component of the propellant.

        Returns:
            Function object with (time, I_23) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(1, 2)

    @property
    def propellant_I_33(self) -> "Function":
        """Inertia tensor I_33 (I_zz) component of the propellant.

        Inertia relative to the e_3 axis (motor body axis), centered at the
        instantaneous propellant center of mass.

        Returns:
            Function object with (time, I_33) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(2, 2)
