import abc
import typing

import numpy as np
import numpy.typing as npt

try:
    import rocketpy
    import rocketpy.motors as rocketpy_motors
except ImportError as e:  # pragma: no cover - exercised only without rocketpy
    raise ImportError("RocketPy adapters require the `rocketpy` package") from e

if typing.TYPE_CHECKING:
    import machwave.simulation as ib_simulation
    from machwave.models.motors import Motor


R = typing.TypeVar("R", bound="ib_simulation.SimulationResult")

ROCKETPY_MOTOR_COORDINATE_SYSTEM = "nozzle_to_combustion_chamber"
RESHAPE_THRUST_CURVE = False
INTERPOLATION_METHOD = "linear"


class RocketPyMotorAdapter(abc.ABC, typing.Generic[R]):
    """
    Abstract base class for RocketPy motor adapters.

    Subclasses must set `_rocketpy_motor_class` to the name of the RocketPy
    Motor class they adapt.
    """

    _rocketpy_motor_class: typing.ClassVar[str] = "Motor"

    def __init_subclass__(cls, **kwargs: typing.Any) -> None:
        """Dynamically inherit from specified RocketPy Motor class."""
        super().__init_subclass__(**kwargs)

        motor_class_name = cls._rocketpy_motor_class
        if not hasattr(rocketpy_motors, motor_class_name):
            raise AttributeError(
                f"RocketPy motors module has no class '{motor_class_name}'"
            )

        motor_class = getattr(rocketpy_motors, motor_class_name)

        if not any(
            isinstance(base, type) and issubclass(base, motor_class)
            for base in cls.__bases__
        ):
            cls.__bases__ = cls.__bases__ + (motor_class,)

    def __init__(self, motor: "Motor", simulation_result: R) -> None:
        """
        Initialize the adapter.

        Args:
            motor: The machwave motor.
            simulation_result: The machwave simulation result.
        """
        self.motor = motor
        self.simulation_result = simulation_result

        attrs = self._get_rocketpy_attributes()
        super().__init__(**attrs)

    def _get_rocketpy_attributes(self) -> dict[str, typing.Any]:
        """Extract motor attributes and time series compatible with RocketPy."""
        time = self.simulation_result.time
        thrust = self.simulation_result.thrust

        thrust_chamber = self.motor.thrust_chamber
        nozzle = thrust_chamber.nozzle

        thrust_source = np.column_stack((time, thrust))

        # Axial position of the dry mass center of gravity.
        # Both machwave and RocketPy use nozzle exit as origin, positive toward the
        # bulkhead ("nozzle_to_combustion_chamber" orientation).
        center_of_dry_mass_position = (
            thrust_chamber.center_of_gravity_coordinate[0]
            if thrust_chamber.center_of_gravity_coordinate is not None
            else 0.0
        )

        return {
            "thrust_source": thrust_source,
            "dry_inertia": (0.0, 0.0, 0.0),  # TODO: Calculate dry mass inertia tensor
            "nozzle_radius": nozzle.outlet_diameter / 2,
            "center_of_dry_mass_position": center_of_dry_mass_position,
            "dry_mass": self.motor.get_dry_mass(),
            "nozzle_position": 0.0,
            "burn_time": (time[0], self.simulation_result.thrust_time),
            "reshape_thrust_curve": RESHAPE_THRUST_CURVE,
            "interpolation_method": INTERPOLATION_METHOD,
            "coordinate_system_orientation": ROCKETPY_MOTOR_COORDINATE_SYSTEM,
            "reference_pressure": self.simulation_result.exit_pressure[0],
        }

    @property
    def exhaust_velocity(self) -> rocketpy.Function:
        """
        Return exhaust velocity as a function of time.

        Computed as total impulse divided by propellant initial mass,
        assumed constant and discretized over the burn time.

        Returns:
            Exhaust velocity [m/s] as a function of time.
        """
        v_exh = self.simulation_result.total_impulse / self.propellant_initial_mass
        return rocketpy.Function(v_exh).set_discrete_based_on_model(self.thrust)  # type: ignore[attr-defined]

    @property
    def propellant_initial_mass(self) -> float:
        """Return the initial propellant mass [kg]."""
        return self.simulation_result.initial_propellant_mass

    @property
    def center_of_propellant_mass(self) -> rocketpy.Function:
        """
        Return the propellant center of mass axial position over time.

        Uses pre-computed values from the simulation result, extracts the
        x-coordinate (axial position) from the propellant's center of gravity
        over time.

        Returns:
            `rocketpy.Function` with (time, position) data [m].
        """
        time = self.simulation_result.time
        center_positions = np.asarray(
            self.simulation_result.propellant_cog[:, 0],  # type: ignore[attr-defined]
            dtype=np.float64,
        ).copy()

        # Replace NaN/Inf values with last valid value (propellant burned out)
        mask = np.isfinite(center_positions)
        if not mask.all():
            last_valid_idx = np.where(mask)[0][-1] if mask.any() else 0
            center_positions[~mask] = center_positions[last_valid_idx]

        data = np.column_stack((time, center_positions))
        return rocketpy.Function(data)

    def _get_inertia_tensor_over_time(self) -> npt.NDArray[np.float64]:
        """
        Return pre-computed inertia tensors from the simulation result.

        Returns:
            Array of shape `(n_timesteps, 3, 3)` containing inertia tensors.
        """
        tensors = np.asarray(
            self.simulation_result.propellant_moi,  # type: ignore[attr-defined]
            dtype=np.float64,
        ).copy()

        # Replace NaN/Inf values with last valid tensor (propellant burned out)
        for i in range(tensors.shape[0]):
            if not np.isfinite(tensors[i]).all():
                if i > 0:
                    tensors[i] = tensors[i - 1]
                else:
                    tensors[i] = np.zeros((3, 3))

        return tensors

    def _get_propellant_inertia_component(self, i: int, j: int) -> rocketpy.Function:
        """
        Return a single component of the propellant inertia tensor over time.

        Args:
            i: First index (0, 1, or 2).
            j: Second index (0, 1, or 2).

        Returns:
            `rocketpy.Function` with (time, I_ij) data [kg-m^2].
        """
        time = self.simulation_result.time
        inertia_tensors = self._get_inertia_tensor_over_time()
        I_values = inertia_tensors[:, i, j]
        data = np.column_stack((time, I_values))
        return rocketpy.Function(data)

    @property
    def propellant_I_11(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_11` (`I_xx`) of the propellant over time.

        Inertia relative to the e_1 axis (perpendicular to motor body axis), centered at
        the instantaneous propellant center of mass.

        Returns:
            `rocketpy.Function` with (time, I_11) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 0)

    @property
    def propellant_I_12(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_12` (`I_xy`) of the propellant over time.

        Returns:
            `rocketpy.Function` with (time, I_12) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 1)

    @property
    def propellant_I_13(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_13` (`I_xz`) of the propellant over time.

        Returns:
            `rocketpy.Function` with (time, I_13) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(0, 2)

    @property
    def propellant_I_22(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_22` (`I_yy`) of the propellant over time.

        Inertia relative to the e_2 axis (perpendicular to motor body axis), centered at
        the instantaneous propellant center of mass.

        Returns:
            `rocketpy.Function` with (time, I_22) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(1, 1)

    @property
    def propellant_I_23(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_23` (`I_yz`) of the propellant over time.

        Returns:
            `rocketpy.Function` with (time, I_23) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(1, 2)

    @property
    def propellant_I_33(self) -> rocketpy.Function:
        """
        Return inertia tensor `I_33` (`I_zz`) of the propellant over time.

        Inertia relative to the e_3 axis (motor body axis), centered at the
        instantaneous propellant center of mass.

        Returns:
            `rocketpy.Function` with (time, I_33) data [kg-m^2].
        """
        return self._get_propellant_inertia_component(2, 2)
