from abc import ABC, abstractmethod

import numpy as np

from machwave.models.motors import Motor


class MotorState(ABC):
    """
    Defines a particular motor operation. Stores and processes all attributes
    obtained from the simulation.
    """

    # Per-step accumulators built up as Python lists during the simulation
    # loop (O(1) append) and converted to np.ndarray once via _finalize().
    _ARRAY_ATTRS: tuple[str, ...] = (
        "t",
        "m_prop",
        "P_0",
        "P_exit",
        "C_f",
        "C_f_ideal",
        "thrust",
    )

    def __init__(
        self,
        motor: Motor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
        other_losses: float,
    ) -> None:
        """
        Initializes attributes for the motor operation.
        Each motor category will contain a particular set of attributes.
        """
        self.motor = motor
        self.other_losses = other_losses

        self.t: list[float] = [0.0]  # time vector

        self.m_prop: list[float] = [motor.initial_propellant_mass]
        self.P_0: list[float] = [initial_pressure]
        self.P_exit: list[float] = [initial_atmospheric_pressure]

        # Thrust coefficients and thrust:
        self.C_f: list[float] = [0.0]
        self.C_f_ideal: list[float] = [0.0]
        self.thrust: list[float] = [0.0]

        # Thrust time:
        self._thrust_time = None

        # If the propellant mass is non zero, 'end_thrust' must be False,
        # since there is still thrust being produced.
        # After the propellant has finished burning and the thrust chamber has
        # stopped producing supersonic flow, 'end_thrust' is changed to True
        # value and the internal ballistics section of the while loop below
        # stops running.
        self.end_thrust = False
        self.end_burn = False

    def _finalize(self) -> None:
        """Convert accumulated lists into ndarrays for downstream consumers."""
        for name in self._ARRAY_ATTRS:
            value = getattr(self, name)
            if not isinstance(value, np.ndarray):
                setattr(self, name, np.asarray(value))

    @abstractmethod
    def get_m_dot_in(self) -> float:
        """Mass flow rate into the combustion chamber [kg/s]."""
        pass

    @abstractmethod
    def run_timestep(self, *args, **kwargs) -> None:
        """
        Calculates and stores operational parameters in the corresponding
        vectors.

        This method will depend on the motor category. While a SRM will have
        to use/store operational parameters such as burn area and propellant
        volume, a HRE or LRE would not have to.

        When executed, the method must increment the necessary attributes
        according to a differential property (time, distance or other).
        """
        pass

    @abstractmethod
    def print_results(self) -> None:
        """
        Prints results obtained during simulation/operation.
        """
        pass

    @property
    def initial_propellant_mass(self) -> float:
        """Get the initial propellant mass [kg]."""
        return self.motor.initial_propellant_mass

    @property
    def thrust_time(self) -> float:
        """Total time of thrust production [s]."""
        if self._thrust_time is None:
            raise ValueError("Thrust time has not been set, run the simulation.")

        return self._thrust_time
