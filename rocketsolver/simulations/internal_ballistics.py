# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.models.propulsion import Motor
from rocketsolver.operations.internal_ballistics import MotorOperation
from rocketsolver.simulations import Simulation, SimulationParameters
from rocketsolver.utils.classes import get_motor_operation_class


class InternalBallisticsParams(SimulationParameters):
    def __init__(
        self,
        d_t: float,
        igniter_pressure: float,
        external_pressure: float,
    ) -> None:
        super().__init__()

        self.d_t = d_t
        self.igniter_pressure = igniter_pressure
        self.external_pressure = external_pressure


class InternalBallistics(Simulation):
    def __init__(
        self,
        motor: Motor,
        params: InternalBallisticsParams,
    ) -> None:
        super().__init__(params=params)

        self.motor = motor

        self.t = np.array([0])

    def get_motor_operation(self) -> MotorOperation:
        """
        Will depend on the type of the motor (SR, HRE or LRE).
        """
        motor_operation_class = get_motor_operation_class(self.motor)

        return motor_operation_class(
            motor=self.motor,
            initial_pressure=self.params.igniter_pressure,
            initial_atmospheric_pressure=self.params.external_pressure,
        )

    def run(self):
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters.
        """
        self.motor_operation = self.get_motor_operation()

        i = 0

        while not self.motor_operation.end_thrust:
            self.t = np.append(
                self.t, self.t[i] + self.params.d_t
            )  # new time value

            self.motor_operation.iterate(
                self.params.d_t,
                self.params.external_pressure,
            )

            i += 1

        return (self.t, self.motor_operation)

    def print_results(self):
        """
        Prints the results of the simulation.
        """
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")
        self.motor_operation.print_results()
