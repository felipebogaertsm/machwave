from dataclasses import dataclass

import machwave.models.motors as motors
import machwave.simulation.liquid.states as liquid_states
import machwave.simulation.results as simulation_results
import machwave.simulation.solid.states as solid_states
import machwave.simulation.states as simulation_states


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
        motor: motors.Motor,
        params: InternalBallisticsSimulationParams,
    ) -> None:
        """
        Initialize an internal ballistics simulation.

        Args:
            motor: Motor model to simulate.
            params: Simulation parameters.
        """
        self.motor: motors.Motor = motor
        self.params: InternalBallisticsSimulationParams = params

    def _build_motor_state(self) -> simulation_states.MotorState:
        """Build the motor state matching the configured motor type."""
        if isinstance(self.motor, motors.SolidMotor):
            return solid_states.SolidMotorState(
                motor=self.motor,
                igniter_pressure=self.params.igniter_pressure,
                external_pressure=self.params.external_pressure,
                other_losses=self.params.other_losses,
            )
        if isinstance(self.motor, motors.LiquidEngine):
            return liquid_states.LiquidEngineState(
                motor=self.motor,
                igniter_pressure=self.params.igniter_pressure,
                external_pressure=self.params.external_pressure,
                other_losses=self.params.other_losses,
            )
        raise ValueError("Unsupported motor type.")

    def run(self) -> simulation_results.SimulationResult:
        """Run the simulation to thrust termination and return its result."""
        motor_state = self._build_motor_state()

        d_t = self.params.d_t
        external_pressure = self.params.external_pressure

        while not motor_state.end_thrust:
            motor_state.run_timestep(d_t, external_pressure)

        return motor_state.build_result()
