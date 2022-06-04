# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np


class BallisticOperation:
    """
    Stores and processes a ballistics operation (aka flight).
    """

    def __init__(self) -> None:
        """
        Initializes attributes for the operation.
        """
        self.t = np.array([0])  # time vector

        self.P_ext = np.array([])  # external pressure
        self.rho_air = np.array([])  # air density
        self.g = np.array([])  # acceleration of gravity
        self.vehicle_mass = np.array([])  # total mass of the vehicle

        # Spacial params:
        self.y = np.array([0])  # altitude, AGL
        self.v = np.array([0])  # velocity
        self.acceleration = np.array([0])  # acceleration
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
