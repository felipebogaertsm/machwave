# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Optional

import numpy as np

from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.rocket import Rocket3D
from rocketsolver.operations.internal_ballistics import MotorOperation
from rocketsolver.operations.ballistics._6dof import Ballistic6DOFOperation
from rocketsolver.simulations import Simulation
from rocketsolver.utils.classes import get_motor_operation_class


class Ballistic6DOFSimulation(Simulation):
    def __init__(
        self,
        rocket: Rocket3D,
        atmosphere: Atmosphere,
        d_t: float,
        initial_elevation_amsl: float,
        rail_length: float,
        launch_angle: float,
        heading_angle: float,
        igniter_pressure: Optional[float] = 1.5e6,
    ) -> None:
        self.rocket = rocket
        self.atmosphere = atmosphere
        self.d_t = d_t
        self.initial_elevation_amsl = initial_elevation_amsl
        self.rail_length = rail_length
        self.launch_angle = launch_angle
        self.heading_angle = heading_angle
        self.igniter_pressure = igniter_pressure

        self.t = np.array([0])

    def get_motor_operation(self) -> MotorOperation:
        """
        Will depend on the type of the motor (SR, HRE or LRE).
        """
        motor_operation_class = get_motor_operation_class(
            self.rocket.propulsion
        )

        return motor_operation_class(
            motor=self.rocket.propulsion,
            initial_pressure=self.igniter_pressure,
            initial_atmospheric_pressure=self.atmosphere.get_pressure(
                self.initial_elevation_amsl
            ),
        )

    def run(self) -> tuple[np.array, Ballistic6DOFOperation]:
        self.motor_operation = self.get_motor_operation()
        self.ballistic_operation = Ballistic6DOFOperation(
            fuselage=self.rocket.fuselage,
            recovery=self.rocket.recovery,
            atmosphere=self.atmosphere,
            rail_length=self.rail_length,
            motor_dry_mass=self.rocket.propulsion.get_dry_mass(),
            initial_vehicle_mass=60,
        )

        i = 0

        while (
            self.ballistic_operation.position[i][2] >= 0  # altitude >= 0
            or self.motor_operation.m_prop[-1] > 0
        ):
            self.t = np.append(self.t, self.t[i] + self.d_t)  # new time value

            if self.motor_operation.end_thrust is False:
                self.motor_operation.iterate(
                    self.d_t,
                    self.ballistic_operation.P_ext[i],
                )

                propellant_mass = self.motor_operation.m_prop[i]
                thrust = self.motor_operation.thrust[i]
                d_t = self.d_t
            else:
                propellant_mass = 0
                thrust = 0

                # Adding new delta time value for ballistic simulation:
                d_t = self.d_t * self.dd_t
                self.t[-1] = self.t[-2] + self.dd_t * self.d_t

            self.ballistic_operation.iterate(propellant_mass, thrust, d_t)

            i += 1

        return (self.t, self.motor_operation, self.ballistic_operation)

    def print_results(self):
        """
        Prints the results of the simulation.
        """
        print("\nINTERNAL BALLISTICS COUPLED SIMULATION RESULTS")
        self.ballistic_operation.print_results()
