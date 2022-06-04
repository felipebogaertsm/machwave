# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from solvers.ballistics_1d import Ballistics1D


class Ballistic1DOperation:
    """
    Stores and processes a ballistics operation (aka flight).
    """

    def __init__(self, rocket, initial_vehicle_mass) -> None:
        """
        Initializes attributes for the operation.
        """
        self.rocket = rocket
        self.ballistics_solver = Ballistics1D()

        self.t = np.array([0])  # time vector

        self.P_ext = np.array([])  # external pressure
        self.rho_air = np.array([])  # air density
        self.g = np.array([])  # acceleration of gravity
        self.vehicle_mass = np.array(
            [initial_vehicle_mass]
        )  # total mass of the vehicle

        # Spacial params:
        self.y = np.array([0])  # altitude, AGL
        self.v = np.array([0])  # velocity
        self.acceleration = np.array([])  # acceleration
        self.mach_no = np.array([0])  # mach number

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
        rho_air: float,
    ) -> None:
        # Appending the current vehicle mass, consisting of the motor
        # structural mass, mass without the motor and propellant mass.
        vehicle_mass = np.append(
            vehicle_mass,
            propellant_mass
            + self.motor.structure.dry_mass
            + self.rocket.structure.mass_without_motor,
        )

        # Drag properties:
        fuselage_area = self.rocket.fuselage.frontal_area
        fuselage_drag_coeff = self.rocket.fuselage.get_drag_coefficient()
        (
            recovery_drag_coeff,
            recovery_area,
        ) = self.recovery.get_drag_coefficient_and_area(
            height=y, time=t, velocity=v, propellant_mass=propellant_mass
        )

        D = (
            (
                fuselage_area * fuselage_drag_coeff
                + recovery_area * recovery_drag_coeff
            )
            * rho_air[-1]
            * 0.5
        )

        ballistics_results = self.ballistics_solver.solve(
            self.y[-1],
            self.v[-1],
            thrust,
            D,
            self.vehicle_mass[-1],
            self.g[-1],
            self.d_t,
        )

        self.y = np.append(self.y, ballistics_results[0])
        self.v = np.append(self.v, ballistics_results[1])
        self.acceleration = np.append(self.acceleration, ballistics_results[2])

        self.mach_no = np.append(
            self.mach_no,
            self.v[-1] / self.atmosphere.get_sonic_velocity(self.y[-1]),
        )

        if self.y[-1] < 0:
            self.y = np.delete(self.y, -1)
            self.v = np.delete(self.v, -1)
            self.acc = np.delete(self.acc, -1)
            self.t = np.delete(self.t, -1)

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

    @property
    def velocity_out_of_rail(self) -> float:
        """
        Returns the velocity out of the rail.
        """
        return self.v[np.argmax(self.y)]
