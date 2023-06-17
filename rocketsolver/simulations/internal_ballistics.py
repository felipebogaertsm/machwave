import numpy as np

from rocketsolver.models.propulsion import Motor
from rocketsolver.operations.internal_ballistics import MotorOperation
from rocketsolver.simulations import Simulation, SimulationParameters
from rocketsolver.services.factories import get_motor_operation_class


class InternalBallisticsParams(SimulationParameters):
    """
    Parameters for an internal ballistics simulation.

    Attributes:
        d_t (float): Time step.
        igniter_pressure (float): Igniter pressure.
        external_pressure (float): External pressure.
    """

    def __init__(
        self,
        d_t: float,
        igniter_pressure: float,
        external_pressure: float,
    ) -> None:
        super().__init__()
        self.d_t = d_t
        self.igniter_pressure = igniter_pressure
        self.external_pressure = external_pressure


class InternalBallistics(Simulation):
    """
    Internal ballistics simulation class.

    Attributes:
        motor (Motor): The motor object.
        params (InternalBallisticsParams): The simulation parameters.
        t (np.ndarray): Array of time values.
        motor_operation (MotorOperation): The motor operation object.
    """

    def __init__(
        self,
        motor: Motor,
        params: InternalBallisticsParams,
    ) -> None:
        """
        Initializes the InternalBallistics instance.

        Args:
            motor (Motor): The motor object.
            params (InternalBallisticsParams): The simulation parameters.
        """
        super().__init__(params=params)
        self.motor = motor
        self.t = np.array([0])
        self.motor_operation = None

    def get_motor_operation(self) -> MotorOperation:
        """
        Returns the motor operation object based on the type of the motor.

        Returns:
            MotorOperation: The motor operation object.
        """
        motor_operation_class = get_motor_operation_class(self.motor)
        return motor_operation_class(
            motor=self.motor,
            initial_pressure=self.params.igniter_pressure,
            initial_atmospheric_pressure=self.params.external_pressure,
        )

    def run(self):
        """
        Runs the main loop of the simulation, returning the motor operation
        object.

        Returns:
            tuple[np.ndarray, MotorOperation]: A tuple containing the time
                array and the motor operation object.
        """
        self.motor_operation = self.get_motor_operation()

        i = 0

        while not self.motor_operation.end_thrust:
            self.t = np.append(
                self.t, self.t[i] + self.params.d_t
            )  # new time value

            self.motor_operation.iterate(
                self.params.d_t,
                self.params.external_pressure,
            )

            i += 1

        return (self.t, self.motor_operation)

    def print_results(self):
        """
        Prints the results of the simulation.
        """
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")
        self.motor_operation.print_results()
