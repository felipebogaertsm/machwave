from dataclasses import dataclass

from machwave.models.motors import LiquidEngine, Motor, SolidMotor
from machwave.simulation.liquid.states import LiquidEngineState
from machwave.simulation.results import SimulationResult
from machwave.simulation.solid.states import SolidMotorState
from machwave.simulation.states import MotorState


@dataclass
class InternalBallisticsSimulationParams:
    """
    Parameters for an internal ballistics simulation.

    Attributes:
        d_t: Time step.
        igniter_pressure: Igniter pressure.
        external_pressure: External pressure.
        other_losses: Additional losses not covered by specific loss mechanisms,
            as a fraction in [0, 1].
    """

    d_t: float
    igniter_pressure: float
    external_pressure: float
    other_losses: float = 0.05


class InternalBallisticsSimulation:
    """
    Internal ballistics simulation class.

    Attributes:
        motor: Motor object.
        params: Simulation parameters.
    """

    def __init__(
        self,
        motor: Motor,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        """
        Initialize an internal ballistics simulation.

        Args:
            motor: Motor model to simulate.
            params: Simulation parameters.
        """
        self.motor: Motor = motor
        self.params: InternalBallisticsSimulationParams = params

    def _build_motor_state(self) -> MotorState:
        """Build the motor state matching the configured motor type."""
        if isinstance(self.motor, SolidMotor):
            return SolidMotorState(
                motor=self.motor,
                igniter_pressure=self.params.igniter_pressure,
                external_pressure=self.params.external_pressure,
                other_losses=self.params.other_losses,
            )
        if isinstance(self.motor, LiquidEngine):
            return LiquidEngineState(
                motor=self.motor,
                igniter_pressure=self.params.igniter_pressure,
                external_pressure=self.params.external_pressure,
                other_losses=self.params.other_losses,
            )
        raise ValueError("Unsupported motor type.")

    def run(self) -> SimulationResult:
        """Run the simulation to thrust termination and return its result."""
        motor_state = self._build_motor_state()

        d_t = self.params.d_t
        external_pressure = self.params.external_pressure

        while not motor_state.end_thrust:
            motor_state.run_timestep(d_t, external_pressure)

        return motor_state.build_result()
