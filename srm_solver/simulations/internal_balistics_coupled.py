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
from simulations import Simulation
from simulations.operations.ballistics import Ballistics1DOperation
from simulations.operations.internal_ballistics import SRMOperation
from solvers.srm_internal_ballistics import (
    SRMInternalBallisticsSolver,
)
from solvers.ballistics_1d import Ballistics1D


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

    def run(self):
        """
        Runs the main loop of the simulation, returning all the internal and
        external ballistics parameters as instances of the InternalBallistics
        and Ballistics classes.

        The function uses the Runge-Kutta 4th order numerical method for
        solving the differential equations.

        The variable names correspond to what they are commonly reffered to in
        books and papers related to Solid Rocket Propulsion.

        Therefore, PEP8's snake_case will not be followed rigorously.
        """

        # Defining operations and solvers for the simulation:
        if isinstance(self.motor, SolidMotor):
            motor_operation = SRMOperation()

        ballistic_operation = Ballistics1DOperation()

        # PRE CALCULATIONS
        # Variables storing the apogee, apogee time:
        apogee, apogee_time = 0, -1

        i = 0

        while y[i] >= 0 or motor_operation.m_prop[i - 1] > 0:
            t = np.append(t, t[i] + self.d_t)  # append new time value

            # Obtaining the value for the air density, the acceleration of
            # gravity and ext. pressure in function of the current altitude.
            rho_air = np.append(
                rho_air,
                self.atmosphere.get_density(
                    y_amsl=(y[i] + self.initial_elevation_amsl)
                ),
            )
            g = np.append(
                g,
                self.atmosphere.get_gravity(
                    self.initial_elevation_amsl + y[i]
                ),
            )
            P_ext = np.append(
                P_ext,
                self.atmosphere.get_pressure(
                    self.initial_elevation_amsl + y[i]
                ),
            )

            motor_operation.iterate(self.d_t, P_ext)
            ballistic_operation.iterate(motor_operation.m_prop[i])

            if (
                y[i + 1] <= y[i]
                and motor_operation.m_prop[i] == 0
                and apogee == 0
            ):
                apogee = y[i]
                apogee_time = t[np.where(y == apogee)]

            i += 1

        return [motor_operation, ballistic_operation]
