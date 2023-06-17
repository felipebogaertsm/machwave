from rocketsolver.models.propulsion import Motor, SolidMotor
from rocketsolver.operations.internal_ballistics import (
    MotorOperation,
    SRMOperation,
)


def get_motor_operation_class(motor: Motor) -> MotorOperation:
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
        return SRMOperation
    else:
        raise ValueError("Unsupported motor type.")
