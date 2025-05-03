import numpy as np

from machwave.models.propulsion.motors import Motor
from machwave.operations.internal_ballistics import MotorOperation
from machwave.services.factories import get_motor_operation_class
from machwave.simulations import Simulation, SimulationParameters


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
        motor_operation (MotorOperation | None): The motor operation object.
    """

    def __init__(
        self,
        motor: Motor,
        params: InternalBallisticsParams,
    ) -> None:
        super().__init__(params=params)
        self.motor: Motor = motor
        self.params: InternalBallisticsParams = params
        self.t: np.ndarray = np.array([0])
        self.motor_operation: MotorOperation | None = None

    def get_motor_operation(self) -> MotorOperation:
        """
        Returns the motor operation object based on the type of the motor.
        """
        motor_operation_class = get_motor_operation_class(self.motor)
        return motor_operation_class(
            motor=self.motor,
            initial_pressure=self.params.igniter_pressure,
            initial_atmospheric_pressure=self.params.external_pressure,
        )

    def run(self) -> tuple[np.ndarray, MotorOperation]:
        """
        Runs the main loop of the simulation, returning the time array and
        the motor operation object.
        """
        self.motor_operation = self.get_motor_operation()

        i = 0
        while not self.motor_operation.end_thrust:
            self.t = np.append(self.t, self.t[i] + self.params.d_t)

            self.motor_operation.run_timestep(
                self.params.d_t,
                self.params.external_pressure,
            )
            i += 1

        return (self.t, self.motor_operation)

    def print_results(self) -> None:
        """
        Prints the results of the simulation.
        """
        if self.motor_operation is None:
            print(
                "No motor operation results available. Try running the simulation first."
            )
            return

        print("\nINTERNAL BALLISTICS SIMULATION RESULTS")
        self.motor_operation.print_results()
