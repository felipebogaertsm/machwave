# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
The coupled internal ballistics simulation calculates both internal and 
external ballistics parameters simulatneously. 

The main advantage of this strategy is that, while some environmental 
attributes change during flight, they also serve as inputs for the internal 
ballistic of the motor. The main attribute that changes during flight is the 
ambient pressure, which impacts the propellant burn rate inside the motor.
"""

import numpy as np

from models.atmosphere import Atmosphere
from models.propulsion import Motor, SolidMotor
from models.recovery import Recovery
from models.rocket import Rocket
from operations.ballistics import Ballistic1DOperation
from operations.internal_ballistics import SRMOperation
from simulations import Simulation


class InternalBallisticsCoupled(Simulation):
    def __init__(
        self,
        motor: Motor,
        rocket: Rocket,
        recovery: Recovery,
        atmosphere: Atmosphere,
        d_t: float,
        dd_t: float,
        initial_elevation_amsl: float,
        igniter_pressure: float,
        rail_length: float,
    ) -> None:
        self.motor = motor
        self.rocket = rocket
        self.recovery = recovery
        self.atmosphere = atmosphere
        self.d_t = d_t
        self.dd_t = dd_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.igniter_pressure = igniter_pressure
        self.rail_length = rail_length

        self.t = np.array([0])

    def run(self):
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters.
        """

        # Defining operations and solvers for the simulation:
        if isinstance(self.motor, SolidMotor):
            motor_operation_class = SRMOperation

        motor_operation = motor_operation_class(
            motor=self.motor,
            initial_pressure=self.igniter_pressure,
        )

        ballistic_operation = Ballistic1DOperation(
            self.rocket,
            self.recovery,
            self.atmosphere,
            motor_dry_mass=self.motor.structure.dry_mass,
            initial_vehicle_mass=self.rocket.structure.mass_without_motor,
            initial_elevation_amsl=self.initial_elevation_amsl,
        )

        i = 0

        while (
            ballistic_operation.y[i] >= 0 or motor_operation.m_prop[i - 1] > 0
        ):
            print(f"\n\nITERATION #{i}\n\n")

            self.t = np.append(
                self.t, self.t[i] + self.d_t
            )  # append new time value

            motor_operation.iterate(
                self.d_t,
                ballistic_operation.P_ext[i],
            )

            ballistic_operation.iterate(
                motor_operation.m_prop[i],
                motor_operation.thrust[i],
                self.d_t,
            )

            i += 1

        return [self.t, motor_operation, ballistic_operation]
