from abc import ABC, abstractmethod
from typing import TypeAlias

import numpy as np

from machwave.models.motors import Motor

# Python list during the simulation loop (O(1) appends), then converted to
# np.ndarray by convert_simulation_arrays_to_numpy() once the loop ends.
SimulationArray: TypeAlias = list[float]


class MotorState(ABC):
    """
    Defines a particular motor operation. Stores and processes all attributes
    obtained from the simulation.
    """

    # Per-step accumulators built up as Python lists during the simulation
    # loop (O(1) append) and converted to np.ndarray once via convert_simulation_arrays_to_numpy().
    SIMULATION_ARRAY_ATTRIBUTE_NAMES: tuple[str, ...] = (
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

        self.t: SimulationArray = [0.0]  # time vector

        self.m_prop: SimulationArray = [motor.initial_propellant_mass]
        self.P_0: SimulationArray = [initial_pressure]
        self.P_exit: SimulationArray = [initial_atmospheric_pressure]

        # Thrust coefficients and thrust:
        self.C_f: SimulationArray = [0.0]
        self.C_f_ideal: SimulationArray = [0.0]
        self.thrust: SimulationArray = [0.0]

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

    def convert_simulation_arrays_to_numpy(self) -> None:
        """Convert accumulated lists into ndarrays for downstream consumers."""
        for name in self.SIMULATION_ARRAY_ATTRIBUTE_NAMES:
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
