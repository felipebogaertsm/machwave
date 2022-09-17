# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
The 6DOF operation class is still under development.
"""

from typing import Optional

import numpy as np

from . import BallisticOperation
from rocketsolver.models.atmosphere import Atmosphere
from rocketsolver.models.recovery import Recovery
from rocketsolver.models.fuselage import Fuselage3D
from rocketsolver.solvers.ballistics_6d import Ballistics6D
from rocketsolver.utils.math import cumtrapz_matrices, multiply_matrix


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
        self.moment_of_inertia_tensor = fuselage.moment_of_inertia_tensor
        self.vehicle_wind_velocity = np.array(
            [self.get_vehicle_wind_velocity(self.wind_velocity[0])]
        )  # normal, lateral

        # Spacial params - x (altitude), y (North), z (East):
        self.eta_inertial = np.array(  # position, inertial frame
            [
                [
                    [0],  # x (m)
                    [0],  # y (m)
                    [0],  # z (m)
                    [0],  # roll (rad)
                    [np.deg2rad(self.launch_angle)],  # pitch (rad)
                    [-np.deg2rad(self.heading_angle)],  # yaw (rad)
                ]
            ]
        )
        self.velocity_body = np.array(  # velocity, body frame
            [
                [
                    [0],  # x (m/s)
                    [0],  # y (m/s)
                    [0],  # z (m/s)
                    [0],  # roll (rad/s)
                    [0],  # pitch (rad/s)
                    [0],  # yaw (rad/s)
                ]
            ]
        )

        self.velocity_inertial = np.array(
            [
                multiply_matrix(  # velocity, inertial frame
                    self.get_J_matrix(), self.velocity_body[-1]
                )
            ],
        )

        self.tau = np.array(  # forces and moments
            [
                [
                    [0],  # x (kg-m/s-s)
                    [0],  # y (kg-m/s-s)
                    [0],  # z (kg-m/s-s)
                    [0],  # roll (kg-rad/s-s)
                    [0],  # pitch (kg-rad/s-s)
                    [0],  # yaw (kg-rad/s-s)
                ]
            ]
        )

        self.attack_angle = np.array([self.get_attack_angle()])
        self.slip_angle = np.array([self.get_slip_angle()])

        self.velocity_out_of_rail = None

    @property
    def altitude(self) -> float:
        return self.eta_inertial[-1][0]

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
                [
                    wind_velocity[0] * np.sin(heading_angle_rad)
                    + wind_velocity[1] * np.cos(heading_angle_rad)
                ],
                [
                    -wind_velocity[0] * np.cos(heading_angle_rad)
                    + wind_velocity[1] * np.sin(heading_angle_rad)
                ],
                [0],
                [0],
                [0],
                [0],
            ]
        )

    def get_slip_angle(self, index: Optional[int] = -1) -> float:
        """
        :return: slip angle (rad)
        :rtype: float
        """
        velocity_z = self.velocity_body[index][2]
        return np.arcsin(
            velocity_z / np.linalg.norm(self.velocity_body[index][:3])
        )

    def get_attack_angle(self, index: Optional[int] = -1) -> float:
        """
        :return: attack angle (rad)
        :rtype: float
        """
        velocity_x = self.velocity_body[index][0]
        velocity_y = self.velocity_body[index][1]
        return np.arctan(velocity_y / velocity_x)

    def get_moment_matrix(self, index: Optional[int] = -1) -> np.ndarray:
        return np.array(
            [
                [self.vehicle_mass[index], 0, 0, 0, 0, 0],
                [0, self.vehicle_mass[index], 0, 0, 0, 0],
                [0, 0, self.vehicle_mass[index], 0, 0, 0],
                [0, 0, 0, *self.moment_of_inertia_tensor[0]],
                [0, 0, 0, *self.moment_of_inertia_tensor[1]],
                [0, 0, 0, *self.moment_of_inertia_tensor[2]],
            ],
        )

    def get_gravitational_matrix(
        self, index: Optional[int] = -1
    ) -> np.ndarray:
        phi_x = self.eta_inertial[index][3][0]
        phi_y = self.eta_inertial[index][4][0]

        return np.array(
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

    def get_aerodynamic_forces_matrix(
        self, index: Optional[int] = -1
    ) -> np.ndarray:
        C_l_alpha = 0.3
        C_d_0 = 0.4
        C_d_i = 0.3
        C_m_alpha = 0.5

        velocity_modulus = np.linalg.norm(self.velocity_body[index][:3])

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
            return np.array(
                0.5
                * self.rho_air[index]
                * self.fuselage.body_segments[0].frontal_area
                * np.array(
                    [
                        [
                            C_d_0 * velocity_modulus,
                            (C_d_i - C_l_alpha) * self.velocity_body[index][1],
                            (C_d_i - C_l_alpha) * self.velocity_body[index][2],
                            0,
                            0,
                            0,
                        ],
                        [
                            C_d_0 * self.velocity_body[index][1],
                            C_l_alpha * velocity_modulus
                            + (
                                C_d_i
                                * self.velocity_body[index][1] ** 2
                                / velocity_modulus
                            ),
                            C_d_i
                            * self.velocity_body[index][2]
                            * self.velocity_body[index][1]
                            / velocity_modulus,
                            0,
                            0,
                            0,
                        ],
                        [
                            C_d_0 * self.velocity_body[index][2],
                            C_d_i
                            * self.velocity_body[index][2]
                            * self.velocity_body[index][1]
                            / velocity_modulus,
                            C_l_alpha * velocity_modulus
                            + (
                                C_d_i
                                * self.velocity_body[index][2] ** 2
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
        phi_x = self.eta_inertial[index][3][0]
        phi_y = self.eta_inertial[index][4][0]
        phi_z = self.eta_inertial[index][5][0]

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

    def get_coriolis_matrix(self, index: Optional[int] = -1) -> np.ndarray:
        v_x = self.velocity_body[index][0][0]
        v_y = self.velocity_body[index][1][0]
        v_z = self.velocity_body[index][2][0]
        w_x = self.velocity_body[index][3][0]
        w_y = self.velocity_body[index][4][0]
        w_z = self.velocity_body[index][5][0]

        vehicle_mass = self.vehicle_mass[index]

        I_x = self.fuselage.moment_of_inertia_tensor[0][0]
        I_y = self.fuselage.moment_of_inertia_tensor[1][1]

        return np.array(
            [
                [0, 0, 0, 0, vehicle_mass * v_z, -vehicle_mass * v_y],
                [0, 0, 0, -vehicle_mass * v_z, 0, vehicle_mass * v_x],
                [0, 0, 0, vehicle_mass * v_y, -vehicle_mass * v_x, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, -I_y * w_z, 0, I_x * w_x],
                [0, 0, 0, I_y * w_y, -I_x * w_x, 0],
            ],
        )

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
                y_amsl=(self.altitude + self.initial_elevation_amsl)
            ),
        )
        self.g = np.append(
            self.g,
            self.atmosphere.get_gravity(
                self.initial_elevation_amsl + self.altitude
            ),
        )

        self.velocity_body = np.append(
            self.velocity_body,
            [
                self.ballistics_solver.solve(
                    M=self.get_moment_matrix(),
                    C=self.get_coriolis_matrix(),
                    V=self.velocity_body[-1],
                    D=self.get_aerodynamic_forces_matrix(),
                    G=self.get_gravitational_matrix(),
                    tau=self.tau[-1],
                    d_t=d_t,
                )
            ],
            axis=0,
        )

        self.velocity_inertial = np.append(
            self.velocity_inertial,
            [
                multiply_matrix(
                    self.get_J_matrix(),
                    self.velocity_body[-1],
                )
            ],
            axis=0,
        )

        # Find position by integrating velocity:
        self.eta_inertial = np.append(
            self.eta_inertial,
            [
                cumtrapz_matrices(self.velocity_inertial, self.t)
                + self.eta_inertial[-1]
            ],
            axis=0,
        )

        self.attack_angle = np.append(
            self.attack_angle, self.get_attack_angle()
        )
        self.slip_angle = np.append(self.slip_angle, self.get_slip_angle())

        self.P_ext = np.append(
            self.P_ext,
            self.atmosphere.get_pressure(
                self.altitude + self.initial_elevation_amsl
            ),
        )

    def print_results(self) -> None:
        print("No results yet")
