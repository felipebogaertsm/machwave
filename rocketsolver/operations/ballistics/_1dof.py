# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.operations import Operation
from rocketsolver.solvers.ballistics_1d import Ballistics1D


class Ballistic1DOperation(Operation):
    """
    Stores and processes a ballistics operation (aka flight).
    """

    def __init__(
        self,
        rocket,
        recovery,
        atmosphere,
        rail_length,
        motor_dry_mass,
        initial_vehicle_mass,
        initial_elevation_amsl=0,
    ) -> None:
        """
        Initializes attributes for the operation.
        """
        self.rocket = rocket
        self.recovery = recovery
        self.atmosphere = atmosphere
        self.rail_length = rail_length
        self.initial_elevation_amsl = initial_elevation_amsl
        self.motor_dry_mass = motor_dry_mass
        self.ballistics_solver = Ballistics1D()

        self.t = np.array([0])  # time vector

        self.P_ext = np.array(
            [self.atmosphere.get_pressure(initial_elevation_amsl)]
        )  # external pressure
        self.rho_air = np.array(
            [self.atmosphere.get_density(initial_elevation_amsl)]
        )  # air density
        self.g = np.array(
            [self.atmosphere.get_gravity(initial_elevation_amsl)]
        )  # acceleration of gravity
        self.vehicle_mass = np.array(
            [initial_vehicle_mass]
        )  # total mass of the vehicle

        # Spacial params:
        self.y = np.array([0])  # altitude, AGL
        self.v = np.array([0])  # velocity
        self.acceleration = np.array([0])  # acceleration
        self.mach_no = np.array([0])  # mach number

        self.velocity_out_of_rail = None

    @property
    def apogee(self) -> float:
        """
        Returns the apogee of the operation.
        """
        return np.max(self.y)

    @property
    def apogee_time(self) -> float:
        """
        Returns the time of the apogee.
        """
        return self.t[np.argmax(self.y)]

    @property
    def max_velocity(self) -> float:
        """
        Returns the maximum velocity of the operation.
        """
        return np.max(self.v)

    @property
    def max_velocity_time(self) -> float:
        """
        Returns the time of the maximum velocity.
        """
        return self.t[np.argmax(self.v)]

    def iterate(
        self,
        propellant_mass: float,
        thrust: float,
        d_t: float,
    ) -> None:
        self.t = np.append(self.t, self.t[-1] + d_t)  # append new time value

        self.rho_air = np.append(
            self.rho_air,
            self.atmosphere.get_density(
                y_amsl=(self.y[-1] + self.initial_elevation_amsl)
            ),
        )
        self.g = np.append(
            self.g,
            self.atmosphere.get_gravity(
                self.initial_elevation_amsl + self.y[-1]
            ),
        )

        # Appending the current vehicle mass, consisting of the motor
        # structural mass, mass without the motor and propellant mass.
        self.vehicle_mass = np.append(
            self.vehicle_mass,
            propellant_mass
            + self.motor_dry_mass
            + self.rocket.structure.mass_without_motor,
        )

        # Drag properties:
        fuselage_area = self.rocket.fuselage.frontal_area
        fuselage_drag_coeff = self.rocket.fuselage.get_drag_coefficient()
        (
            recovery_drag_coeff,
            recovery_area,
        ) = self.recovery.get_drag_coefficient_and_area(
            height=self.y,
            time=self.t,
            velocity=self.v,
            propellant_mass=propellant_mass,
        )

        D = (
            (
                fuselage_area * fuselage_drag_coeff
                + recovery_area * recovery_drag_coeff
            )
            * self.rho_air[-1]
            * 0.5
        )

        ballistics_results = self.ballistics_solver.solve(
            self.y[-1],
            self.v[-1],
            thrust,
            D,
            self.vehicle_mass[-1],
            self.g[-1],
            d_t,
        )

        height = ballistics_results[0]
        velocity = ballistics_results[1]
        acceleration = ballistics_results[2]

        if height < 0 and len(self.y[self.y > 0]) == 0:
            height = 0
            velocity = 0
            acceleration = 0

        self.y = np.append(self.y, height)
        self.v = np.append(self.v, velocity)
        self.acceleration = np.append(self.acceleration, acceleration)

        self.mach_no = np.append(
            self.mach_no,
            self.v[-1] / self.atmosphere.get_sonic_velocity(self.y[-1]),
        )

        self.P_ext = np.append(
            self.P_ext, self.atmosphere.get_pressure(self.y[-1])
        )

        if self.velocity_out_of_rail is None and self.y[-1] > self.rail_length:
            self.velocity_out_of_rail = self.v[-2]

    def print_results(self) -> None:
        """
        Prints the results of the operation.
        """
        print("\nROCKET BALLISTICS")

        print(f" Apogee: {np.max(self.y):.2f} m")
        print(f" Max. velocity: {np.max(self.v):.2f} m/s")
        print(f" Max. Mach number: {np.max(self.mach_no):.3f}")
        print(f" Max. acceleration: {np.max(self.acceleration) / 9.81:.2f} gs")
        print(f" Time to apogee: {self.apogee_time:.2f} s")
        print(
            f" Velocity out of the rail: {self.velocity_out_of_rail:.2f} m/s"
        )
        print(f" Liftoff mass: {self.vehicle_mass[0]:.3f} kg")
        print(f" Flight time: {self.t[-1]:.2f} s")

    @property
    def apogee_time(self) -> float:
        """
        Returns the time of the apogee.
        """
        return self.t[np.argmax(self.y)]
