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
from operations.internal_ballistics import MotorOperation, SRMOperation
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

    def get_motor_operation(self) -> MotorOperation:
        """
        Will depend on the type of the motor (SR, HRE or LRE).
        """
        if isinstance(self.motor, SolidMotor):
            motor_operation_class = SRMOperation

        return motor_operation_class(
            motor=self.motor,
            initial_pressure=self.igniter_pressure,
        )

    def run(self):
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters.
        """
        motor_operation = self.get_motor_operation()
        ballistic_operation = Ballistic1DOperation(
            self.rocket,
            self.recovery,
            self.atmosphere,
            rail_length=self.rail_length,
            motor_dry_mass=self.motor.structure.dry_mass,
            initial_vehicle_mass=self.rocket.structure.mass_without_motor,
            initial_elevation_amsl=self.initial_elevation_amsl,
        )

        i = 0

        while ballistic_operation.y[i] >= 0 or motor_operation.m_prop[-1] > 0:
            self.t = np.append(self.t, self.t[i] + self.d_t)  # new time value

            if motor_operation.end_thrust is False:
                motor_operation.iterate(
                    self.d_t,
                    ballistic_operation.P_ext[i],
                )

                propellant_mass = motor_operation.m_prop[i]
                thrust = motor_operation.thrust[i]
                d_t = self.d_t
            else:
                propellant_mass = 0
                thrust = 0
                d_t = self.d_t * self.dd_t

            ballistic_operation.iterate(propellant_mass, thrust, d_t)

            i += 1

        return (self.t, motor_operation, ballistic_operation)
