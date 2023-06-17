from rocketsolver.models.propulsion import Motor, SolidMotor
from rocketsolver.operations.internal_ballistics import (
    MotorOperation,
    SRMOperation,
)


def get_motor_operation_class(motor: Motor) -> MotorOperation:
    """
    Will depend on the type of the motor (SRM, HRE or LRE).
    """
    if isinstance(motor, SolidMotor):
        return SRMOperation
