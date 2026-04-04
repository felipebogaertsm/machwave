import numpy as np

from machwave.models.propulsion.motors import LiquidEngine, Motor, SolidMotor
from machwave.states.internal_ballistics import (
    LiquidEngineState,
    MotorState,
    SolidMotorState,
)


class InternalBallisticsParams:
    """Parameters for an internal ballistics simulation.

    Attributes:
        d_t: Time step.
        igniter_pressure: Igniter pressure.
        external_pressure: External pressure.
    """

    def __init__(
        self,
        d_t: float,
        igniter_pressure: float,
        external_pressure: float,
    ) -> None:
        self.d_t = d_t
        self.igniter_pressure = igniter_pressure
        self.external_pressure = external_pressure


def _get_motor_state_class(motor: Motor) -> type[MotorState]:
    """Return the appropriate motor state class based on the motor type.

    Args:
        motor: Motor object.

    Returns:
        Motor state class.

    Raises:
        ValueError: If the motor type is not supported.
    """
    if isinstance(motor, SolidMotor):
        return SolidMotorState
    if isinstance(motor, LiquidEngine):
        return LiquidEngineState
    raise ValueError("Unsupported motor type.")


class InternalBallistics:
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
        params: InternalBallisticsParams,
    ) -> None:
        self.motor: Motor = motor
        self.params: InternalBallisticsParams = params
        self.t: np.ndarray = np.array([0])
        self.motor_state: MotorState | None = None

    def get_motor_state(self) -> MotorState:
        """
        Returns the motor state object based on the type of the motor.
        """
        motor_state_class = _get_motor_state_class(self.motor)
        return motor_state_class(
            motor=self.motor,
            initial_pressure=self.params.igniter_pressure,
            initial_atmospheric_pressure=self.params.external_pressure,
        )

    def run(self) -> tuple[np.ndarray, MotorState]:
        """
        Runs the main loop of the simulation, returning the time array and
        the motor state object.
        """
        self.motor_state = self.get_motor_state()

        i = 0
        while not self.motor_state.end_thrust:
            self.t = np.append(self.t, self.t[i] + self.params.d_t)

            self.motor_state.run_timestep(
                self.params.d_t,
                self.params.external_pressure,
            )
            i += 1

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
