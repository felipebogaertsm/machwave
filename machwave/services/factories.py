from machwave.models.propulsion.motors import Motor, SolidMotor, LiquidEngine
from machwave.operations.internal_ballistics import (
    MotorOperation,
    SolidMotorOperation,
    LiquidEngineOperation,
)


def get_motor_operation_class(motor: Motor) -> type[MotorOperation]:
    """
    Returns the appropriate motor operation class based on the type of motor.

    Args:
        motor (Motor): The motor object.

    Returns:
        MotorOperation: The motor operation class.

    Raises:
        ValueError: If the motor type is not supported.

    Example:
        motor = SolidMotor(...)
        motor_operation_class = get_motor_operation_class(motor)
    """
    if isinstance(motor, SolidMotor):
        return SolidMotorOperation
    if isinstance(motor, LiquidEngine):
        return LiquidEngineOperation
    else:
        raise ValueError("Unsupported motor type.")
