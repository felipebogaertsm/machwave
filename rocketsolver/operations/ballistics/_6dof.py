# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Optional

import numpy as np

from . import BallisticOperation
from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.rocket.fuselage import Fuselage3D
from rocketsolver.solvers.ballistics_6d import Ballistics6D


class Ballistic6DOFOperation(BallisticOperation):
    def __init__(
        self,
        fuselage: Fuselage3D,
        recovery: Recovery,
        atmosphere: Atmosphere,
        rail_length: float,
        motor_dry_mass: float,
        initial_vehicle_mass: float,
        launch_angle: float = 90,
        heading_angle: float = 90,
        initial_elevation_amsl: float = 0,
    ) -> None:
        """
        Initializes attributes for the operation.
        """
        self.fuselage = fuselage
        self.recovery = recovery
        self.atmosphere = atmosphere
        self.rail_length = rail_length
        self.launch_angle = launch_angle
        self.heading_angle = heading_angle
        self.initial_elevation_amsl = initial_elevation_amsl
        self.motor_dry_mass = motor_dry_mass
        self.ballistics_solver = Ballistics6D()

        self.t = np.array([0])  # time vector

        # Atmospheric properties:
        self.P_ext = np.array(
            [self.atmosphere.get_pressure(initial_elevation_amsl)]
        )  # external pressure
        self.rho_air = np.array(
            [self.atmosphere.get_density(initial_elevation_amsl)]
        )  # air density
        self.g = np.array(
            [self.atmosphere.get_gravity(initial_elevation_amsl)]
        )  # acceleration of gravity
        self.wind_velocity = np.array(
            [
                *self.atmosphere.get_wind_velocity(initial_elevation_amsl)
            ].reverse()
        )  # eastward, northward

        # Vehicle params:
        self.vehicle_mass = np.array(
            [initial_vehicle_mass]
        )  # total mass of the vehicle
        self.moment_of_inertia_matrix = fuselage.moment_of_inertia_matrix
        self.vehicle_wind_velocity = np.array(
            [*self.get_vehicle_wind_velocity(self.wind_velocity[0])]
        )  # normal, lateral

        # Spacial params - x (East), y (North), z (altitude):
        self.position = np.array([[0, 0, 0]])  # position (m)
        self.velocity = np.array([[0, 0, 0]])  # velocity (m/s)
        self.angular_velocity = np.array(
            [[0, 0, 0]]
        )  # angular velocity (rad/s)
        self.acceleration = np.array([[0, 0, 0]])  # acceleration (m/s-s)
        self.force = np.array([[0, 0, 0]])  # force (N)
        self.torque = np.array([[0, 0, 0]])  # torque (N-m)
        self.mach_no = np.array([[0, 0, 0]])  # mach number

        # Angles (rad):
        self.phi = np.array(
            [0],  # roll
            [np.deg2rad(self.launch_angle - 90)],  # pitch
            [-np.deg2rad(self.heading_angle)],  # yaw
        )
        self.attack_angle = self.get_attack_angle(self.velocity[0])
        self.slip_angle = self.get_slip_angle(self.velocity[0])

        self.velocity_out_of_rail = None

    def get_vehicle_wind_velocity(
        self, wind_velocity: tuple[float, float]
    ) -> tuple[float, float]:
        """
        :param tuple wind_velocity: (eastward, northward)
        :return: (normal, lateral) wind velocities
        :rtype: tuple[float, float]
        """
        heading_angle_rad = np.deg2rad(self.heading_angle)

        return (
            wind_velocity[0] * np.sin(heading_angle_rad)
            + wind_velocity[1] * np.cos(heading_angle_rad),
            -wind_velocity[0] * np.cos(heading_angle_rad)
            + wind_velocity[1] * np.sin(heading_angle_rad),
        )

    @staticmethod
    def get_slip_angle(velocity: np.ndarray[float]) -> float:
        """
        :return: slip angle (rad)
        :rtype: float
        """
        return np.arcsin(velocity[2] / np.linalg.norm(velocity))

    @staticmethod
    def get_attack_angle(velocity: np.ndarray[float]) -> float:
        """
        :return: attack angle (rad)
        :rtype: float
        """
        return np.arctan(velocity[1] / velocity[0])

    @staticmethod
    def get_moment_matrix(
        vehicle_mass, moment_of_inertia_matrix
    ) -> np.ndarray:
        return np.array(
            [
                [vehicle_mass, 0, 0, 0, 0, 0],
                [0, vehicle_mass, 0, 0, 0, 0],
                [0, 0, vehicle_mass, 0, 0, 0],
                [0, 0, 0, *moment_of_inertia_matrix[0]],
                [0, 0, 0, *moment_of_inertia_matrix[1]],
                [0, 0, 0, *moment_of_inertia_matrix[2]],
            ]
        )

    @staticmethod
    def get_gravitational_matrix(
        vehicle_mass, acc_of_gravity, phi_x, phi_y
    ) -> np.ndarray:
        return (
            -vehicle_mass
            * acc_of_gravity
            * np.array(
                [
                    [-np.sin(phi_y)],
                    [np.cos(phi_y) * np.sin(phi_x)],
                    [np.cos(phi_y) * np.cos(phi_x)],
                    [0],
                    [0],
                    [0],
                ]
            )
        )

    @staticmethod
    def get_aerodynamic_matrix():
        """
        % Matriz de forças aerodinâmicas
        D = 0.5 * rho * Corpo.AreaFoguete * [ Cd0*Va   (Cdi-Clalpha)*vy          (Cdi-Clalpha)*vz          0  0  0
                                              Cd0*vy   Clalpha*Va+(Cdi*vy^2/Va)  Cdi*vz*vy/Va              0  0  0
                                              Cd0*vz   Cdi*vy*vz/Va              Clalpha*Va+(Cdi*vz^2/Va)  0  0  0
                                              0        0                         0                         0  0  0
                                              0        0                        -Cmalpha*cref*Va           0  0  0
                                              0        Cmalpha*cref*Va           0                         0  0  0 ];
        """
        pass

    @staticmethod
    def get_J_matrix(phi_x, phi_y, phi_z) -> np.ndarray[float]:
        return np.array(
            [
                [
                    np.cos(phi_z) * np.cos(phi_y),
                    -np.sin(phi_z) * np.cos(phi_x)
                    + np.cos(phi_z) * np.sin(phi_y) * np.sin(phi_x),
                    np.sin(phi_z) * np.sin(phi_x)
                    + np.cos(phi_z) * np.cos(phi_x) * np.sin(phi_y),
                    0,
                    0,
                    0,
                ],
                [
                    np.sin(phi_z) * np.cos(phi_y),
                    np.cos(phi_z) * np.cos(phi_x)
                    + np.sin(phi_x) * np.sin(phi_y) * np.sin(phi_z),
                    -np.cos(phi_z) * np.sin(phi_x)
                    + np.sin(phi_y) * np.sin(phi_z) * np.cos(phi_x),
                    0,
                    0,
                    0,
                ],
                [
                    -np.sin(phi_y),
                    np.cos(phi_y) * np.sin(phi_x),
                    np.cos(phi_y) * np.cos(phi_x),
                    0,
                    0,
                    0,
                ],
                [
                    0,
                    0,
                    0,
                    1,
                    np.sin(phi_x) * np.tan(phi_y),
                    np.cos(phi_x) * np.tan(phi_y),
                ],
                [
                    0,
                    0,
                    0,
                    0,
                    np.cos(phi_x),
                    -np.sin(phi_x),
                ],
                [
                    0,
                    0,
                    0,
                    0,
                    np.sin(phi_x) / np.cos(phi_y),
                    np.cos(phi_x) / np.cos(phi_y),
                ],
            ]
        )

    def get_velocity_matrix(self, index: Optional[int] = -1):
        return np.array([*self.velocity[index], *self.angular_velocity[index]])

    def get_force_matrix(self, index: Optional[int] = -1):
        return np.array([*self.force[index], *self.torque[index]])

    def get_inertial_ref_position_matrix(self, index: Optional[int] = -1):
        return np.array([*self.position[index], *self.phi[index]])

    @property
    def apogee(self) -> float:
        pass

    @property
    def apogee_time(self) -> float:
        pass

    @property
    def max_velocity(self) -> float:
        pass

    @property
    def max_velocity_time(self) -> float:
        pass

    @property
    def apogee_time(self) -> float:
        pass

    def iterate(
        self,
        propellant_mass: float,
        thrust: float,
        d_t: float,
    ) -> None:
        self.t = np.append(self.t, self.t[-1] + d_t)  # append new time value
