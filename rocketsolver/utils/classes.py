# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from rocketsolver.models.propulsion import Motor, SolidMotor
from rocketsolver.operations.internal_ballistics import (
    MotorOperation,
    SRMOperation,
)


def get_motor_operation_class(motor: Motor) -> MotorOperation:
    """
    Will depend on the type of the motor (SR, HRE or LRE).
    """
    if isinstance(motor, SolidMotor):
        return SRMOperation
