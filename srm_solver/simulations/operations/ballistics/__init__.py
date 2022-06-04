# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC

import numpy as np


class BallisticOperation:
    """
    Stores and processes a ballistics operation (aka flight).
    """

    def __init__(self) -> None:
        """
        Initializes attributes for the operation.
        """
        self.t = np.array([])  # time vector

        self.P_ext = np.array([])  # external pressure
        self.rho_air = np.array([])  # air density
        self.g = np.array([])  # acceleration of gravity
        self.vehicle_mass = np.array([])  # total mass of the vehicle

        # Spacial params:
        self.y = np.array([0])  # altitude, AGL
        self.v = np.array([0])  # velocity
        self.mach_no = np.array([0])  # mach number
