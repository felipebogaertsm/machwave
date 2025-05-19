from machwave.models.propulsion.motors import LiquidEngine, Motor, SolidMotor
from machwave.states.internal_ballistics import (
    LiquidEngineState,
    MotorState,
    SolidMotorState,
)


def get_motor_state_class(motor: Motor) -> type[MotorState]:
    """
    Returns the appropriate motor state class based on the type of motor.

    Args:
        motor (Motor): The motor object.

    Returns:
        MotorState: The motor state class.

    Raises:
        ValueError: If the motor type is not supported.

    Example:
        motor = SolidMotor(...)
        motor_state_class = get_motor_state_class(motor)
    """
    if isinstance(motor, SolidMotor):
        return SolidMotorState
    if isinstance(motor, LiquidEngine):
        return LiquidEngineState
    else:
        raise ValueError("Unsupported motor type.")
