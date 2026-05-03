from dataclasses import dataclass

import numpy as np

from machwave.models.motors import Motor
from machwave.states import MotorState


@dataclass
class InternalBallisticsSimulationParams:
    """Parameters for an internal ballistics simulation.

    Attributes:
        d_t: Time step.
        igniter_pressure: Igniter pressure.
        external_pressure: External pressure.
        other_losses: Additional losses not covered by specific loss mechanisms [%].
    """

    d_t: float
    igniter_pressure: float
    external_pressure: float
    other_losses: float = 12.0


class InternalBallisticsSimulation:
    """Internal ballistics simulation class.

    Attributes:
        motor: Motor object.
        params: Simulation parameters.
        t: Array of time values.
        motor_state: Motor state object.
    """

    def __init__(
        self,
        motor: Motor,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        self.motor: Motor = motor
        self.params: InternalBallisticsSimulationParams = params
        self.t: np.ndarray = np.array([0.0])
        self.motor_state: MotorState | None = None

    def get_motor_state(self) -> MotorState:
        """
        Returns the motor state object based on the type of the motor.
        """
        return self.motor.create_state(self.params)

    def run(self) -> tuple[np.ndarray, MotorState]:
        """
        Runs the main loop of the simulation, returning the time array and
        the motor state object.
        """
        self.motor_state = self.get_motor_state()

        d_t = self.params.d_t
        external_pressure = self.params.external_pressure
        t_values: list[float] = [0.0]

        while not self.motor_state.end_thrust:
            t_values.append(t_values[-1] + d_t)
            self.motor_state.run_timestep(d_t, external_pressure)

        self.t = np.asarray(t_values)
        self.motor_state.convert_simulation_arrays_to_numpy()

        return (self.t, self.motor_state)

    def print_results(self) -> None:
        """
        Prints the results of the simulation.
        """
        if self.motor_state is None:
            print("No motor state results available. Try running the simulation first.")
            return

        print("\nINTERNAL BALLISTICS SIMULATION RESULTS")
        self.motor_state.print_results()
