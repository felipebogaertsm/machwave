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
from rocketsolver.models.fuselage import Fuselage3D
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
            [self.atmosphere.get_wind_velocity(initial_elevation_amsl)]
        )  # eastward, northward

        # Vehicle params:
        self.vehicle_mass = np.array(
            [initial_vehicle_mass]
        )  # total mass of the vehicle
        self.moment_of_inertia_matrix = fuselage.moment_of_inertia_matrix
        self.vehicle_wind_velocity = np.array(
            [self.get_vehicle_wind_velocity(self.wind_velocity[0])]
        )  # normal, lateral

        # Spacial params - x (East), y (North), z (altitude):
        self.position = np.array([[0, 0, 0]])  # position (m) - x, y, z
        self.velocity = np.array([[1, 0, 0]])  # velocity (m/s)
        self.angular_velocity = np.array(
            [[0, 0, 0]]
        )  # angular velocity (rad/s)
        self.acceleration = np.array([[0, 0, 0]])  # acceleration (m/s-s)
        self.force = np.array([[0, 0, 0]])  # force (N)
        self.torque = np.array([[0, 0, 0]])  # torque (N-m)
        self.mach_no = np.array([[0, 0, 0]])  # mach number

        # Angles (rad):
        self.phi = np.array(
            [
                [
                    0,  # roll
                    np.deg2rad(self.launch_angle),  # pitch
                    -np.deg2rad(self.heading_angle),  # yaw
                ],
            ]
        )
        self.attack_angle = self.get_attack_angle()
        self.slip_angle = self.get_slip_angle()

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

        return np.array(
            [
                wind_velocity[0] * np.sin(heading_angle_rad)
                + wind_velocity[1] * np.cos(heading_angle_rad),
                -wind_velocity[0] * np.cos(heading_angle_rad)
                + wind_velocity[1] * np.sin(heading_angle_rad),
                0,
                0,
                0,
                0,
            ]
        )

    def get_slip_angle(self, index: Optional[int] = -1) -> float:
        """
        :return: slip angle (rad)
        :rtype: float
        """
        velocity_z = self.velocity[index][2]
        return np.arcsin(velocity_z / np.linalg.norm(self.velocity[index]))

    def get_attack_angle(self, index: Optional[int] = -1) -> float:
        """
        :return: attack angle (rad)
        :rtype: float
        """
        velocity_x = self.velocity[index][0]
        velocity_y = self.velocity[index][1]
        return np.arctan(velocity_y / velocity_x)

    def get_moment_matrix(self, index: Optional[int] = -1) -> np.ndarray:
        return np.array(
            [
                [self.vehicle_mass[index], 0, 0, 0, 0, 0],
                [0, self.vehicle_mass[index], 0, 0, 0, 0],
                [0, 0, self.vehicle_mass[index], 0, 0, 0],
                [0, 0, 0, *self.moment_of_inertia_matrix[0]],
                [0, 0, 0, *self.moment_of_inertia_matrix[1]],
                [0, 0, 0, *self.moment_of_inertia_matrix[2]],
            ]
        )

    def get_gravitational_matrix(
        self, index: Optional[int] = -1
    ) -> np.ndarray:
        phi_x = self.phi[index][0]
        phi_y = self.phi[index][1]

        return (
            -self.vehicle_mass[index]
            * self.g[index]
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

    def get_aerodynamic_forces_matrix(self, index: Optional[int] = -1):
        C_l_alpha = 0.3
        C_d_0 = 0.4
        C_d_i = 0.3
        C_m_alpha = 0.5

        velocity_modulus = np.linalg.norm(self.velocity[index])

        if velocity_modulus == 0:
            return np.array(
                [
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0],
                ]
            )
        else:
            return (
                0.5
                * self.rho_air[index]
                * self.fuselage.body_segments[0].frontal_area
                * np.array(
                    [
                        [
                            C_d_0 * velocity_modulus,
                            (C_d_i - C_l_alpha) * self.velocity[index][1],
                            (C_d_i - C_l_alpha) * self.velocity[index][2],
                            0,
                            0,
                            0,
                        ],
                        [
                            C_d_0 * self.velocity[index][1],
                            C_l_alpha * velocity_modulus
                            + (
                                C_d_i
                                * self.velocity[index][1] ** 2
                                / velocity_modulus
                            ),
                            C_d_i
                            * self.velocity[index][2]
                            * self.velocity[index][1]
                            / velocity_modulus,
                            0,
                            0,
                            0,
                        ],
                        [
                            C_d_0 * self.velocity[index][2],
                            C_d_i
                            * self.velocity[index][2]
                            * self.velocity[index][1]
                            / velocity_modulus,
                            C_l_alpha * velocity_modulus
                            + (
                                C_d_i
                                * self.velocity[index][2] ** 2
                                / velocity_modulus
                            ),
                            0,
                            0,
                            0,
                        ],
                        [
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                        ],
                        [
                            0,
                            0,
                            -C_m_alpha
                            * self.fuselage.body_segments[0].fins.base_length
                            * velocity_modulus,
                            0,
                            0,
                            0,
                        ],
                        [
                            0,
                            C_m_alpha
                            * self.fuselage.body_segments[0].fins.base_length
                            * velocity_modulus,
                            0,
                            0,
                            0,
                            0,
                        ],
                    ]
                )
            )

    def get_J_matrix(self, index: Optional[int] = -1) -> np.ndarray:
        phi_x = self.phi[index][0]
        phi_y = self.phi[index][1]
        phi_z = self.phi[index][2]

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

    def get_coriolis_matrix(self, index: Optional[int] = -1):
        v_x = self.velocity[index][0]
        v_y = self.velocity[index][1]
        v_z = self.velocity[index][2]
        w_x = self.angular_velocity[index][0]
        w_y = self.angular_velocity[index][1]
        w_z = self.angular_velocity[index][2]

        vehicle_mass = self.vehicle_mass[index]

        I_x = self.fuselage.moment_of_inertia_matrix[0][0]
        I_y = self.fuselage.moment_of_inertia_matrix[1][1]

        return np.array(
            [
                [0, 0, 0, 0, vehicle_mass * v_z, -vehicle_mass * v_y],
                [0, 0, 0, -vehicle_mass * v_z, 0, vehicle_mass * v_x],
                [0, 0, 0, vehicle_mass * v_y, -vehicle_mass * v_x, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, -I_y * w_z, 0, I_x * w_x],
                [0, 0, 0, I_y * w_y, -I_x * w_x, 0],
            ]
        )

    def get_velocity_matrix(self, index: Optional[int] = -1):
        return np.array(
            [[*self.velocity[index], *self.angular_velocity[index]]]
        )

    def get_force_matrix(self, index: Optional[int] = -1):
        return np.array([[*self.force[index], *self.torque[index]]])

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

        self.rho_air = np.append(
            self.rho_air,
            self.atmosphere.get_density(
                y_amsl=(self.position[-1][2] + self.initial_elevation_amsl)
            ),
        )
        self.g = np.append(
            self.g,
            self.atmosphere.get_gravity(
                self.initial_elevation_amsl + self.position[-1][2]
            ),
        )

        self.velocity = np.append(
            self.velocity,
            self.ballistics_solver.solve(
                M=self.get_moment_matrix(),
                C=self.get_coriolis_matrix(),
                V=self.get_velocity_matrix(),
                D=self.get_aerodynamic_forces_matrix(),
                G=self.get_gravitational_matrix(),
                tau=self.get_force_matrix(),
                d_t=d_t,
            ),
        )

        print(self.velocity)

        exit()

    def print_results(self) -> None:
        print("No results yet")
