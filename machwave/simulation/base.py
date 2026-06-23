from dataclasses import dataclass

import machwave.models.motors as motors
import machwave.simulation.biliquid.states as biliquid_states
import machwave.simulation.results as simulation_results
import machwave.simulation.solid.states as solid_states
import machwave.simulation.states as simulation_states

MAX_TIME_STEP = 0.01  # s
SEA_LEVEL_PRESSURE = 101_325.0  # Pa


@dataclass
class InternalBallisticsSimulationParams:
    """
    Parameters for an internal ballistics simulation.

    Attributes:
        d_t: Time step [s].
        igniter_pressure: Igniter pressure [Pa].
        external_pressure: External pressure [Pa].
    """

    d_t: float
    igniter_pressure: float
    external_pressure: float

    def __post_init__(self) -> None:
        """
        Validate the simulation parameters.

        Raises:
            ValueError: If any field is outside its valid physical range.
        """
        if not 0.0 < self.d_t <= MAX_TIME_STEP:
            raise ValueError(f"d_t must be in (0, {MAX_TIME_STEP}] s, got {self.d_t}")

        if self.igniter_pressure < SEA_LEVEL_PRESSURE:
            raise ValueError(
                f"igniter_pressure must be at least {SEA_LEVEL_PRESSURE} Pa, got "
                f"{self.igniter_pressure}"
            )

        if self.external_pressure < 0.0:
            raise ValueError(
                f"external_pressure must be non-negative, got {self.external_pressure}"
            )


class InternalBallisticsSimulation:
    """
    Internal ballistics simulation class.

    Attributes:
        motor: Motor object.
        params: Simulation parameters.
    """

    _STATE_CLASS_BY_MOTOR_TYPE = (
        (motors.SolidMotor, solid_states.SolidMotorState),
        (motors.BiliquidEngine, biliquid_states.BiliquidEngineState),
    )

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
        state_kwargs = {
            "motor": self.motor,
            "igniter_pressure": self.params.igniter_pressure,
            "external_pressure": self.params.external_pressure,
        }
        for motor_type, state_class in self._STATE_CLASS_BY_MOTOR_TYPE:
            if isinstance(self.motor, motor_type):
                return state_class(**state_kwargs)
        raise ValueError(f"Unsupported motor type: {type(self.motor).__name__}.")

    def run(self) -> simulation_results.SimulationResult:
        """Run the simulation to thrust termination and return its result."""
        motor_state = self._build_motor_state()

        d_t = self.params.d_t
        external_pressure = self.params.external_pressure

        while not motor_state.end_thrust:
            motor_state.run_timestep(d_t, external_pressure)

        return motor_state.build_result()
