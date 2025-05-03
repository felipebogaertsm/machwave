from abc import abstractmethod

import numpy as np

from machwave.models.propulsion.motors import Motor
from machwave.operations import Operation


class MotorOperation(Operation):
    """
    Defines a particular motor operation. Stores and processes all attributes
    obtained from the simulation.
    """

    def __init__(
        self,
        motor: Motor,
        initial_pressure: float,
        initial_atmospheric_pressure: float,
    ) -> None:
        """
        Initializes attributes for the motor operation.
        Each motor category will contain a particular set of attributes.
        """
        self.motor = motor

        self.t = np.array([0])  # time vector

        self.m_prop = np.array([motor.initial_propellant_mass])  # propellant mass
        self.P_0 = np.array([initial_pressure])  # chamber stagnation pressure
        self.P_exit = np.array([initial_atmospheric_pressure])  # exit pressure

        # Thrust coefficients and thrust:
        self.C_f = np.array([0])  # thrust coefficient
        self.C_f_ideal = np.array([0])  # ideal thrust coefficient
        self.thrust = np.array([0])  # thrust force (N)

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
        """
        Get the initial propellant mass.

        Returns:
            float: The initial propellant mass.
        """
        return self.motor.initial_propellant_mass

    @property
    def thrust_time(self) -> float:
        """
        Total time of thrust production.

        Returns:
            float: The thrust time.
        """
        if self._thrust_time is None:
            raise ValueError("Thrust time has not been set, run the simulation.")

        return self._thrust_time
