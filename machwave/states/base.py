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

    Each motor category provides its own ``Motor.create_state`` that
    constructs the matching ``MotorState``; the simulation layer never picks
    a state class itself.
    """

    SIMULATION_ARRAY_ATTRIBUTE_NAMES: tuple[str, ...] = (
        "t",
        "propellant_mass",
        "chamber_pressure",
        "exit_pressure",
        "thrust_coefficient",
        "thrust_coefficient_ideal",
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

        self.t: SimulationArray = [0.0]

        self.propellant_mass: SimulationArray = [motor.initial_propellant_mass]
        self.chamber_pressure: SimulationArray = [initial_pressure]
        self.exit_pressure: SimulationArray = [initial_atmospheric_pressure]

        self.thrust_coefficient: SimulationArray = [0.0]
        self.thrust_coefficient_ideal: SimulationArray = [0.0]
        self.thrust: SimulationArray = [0.0]

        self._thrust_time = None

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
