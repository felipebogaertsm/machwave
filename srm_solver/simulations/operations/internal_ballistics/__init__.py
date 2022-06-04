# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC

import numpy as np


class MotorOperation(ABC):
    """
    Defines a particular motor operation. Stores and processes all attributes
    obtained from the simulation.
    """

    def __init__(self) -> None:
        """
        Initializes attributes for the motor operation.
        Each motor category will contain a particular set of attributes.
        """
        self.t = np.array([])  # time vector

        self.V_0 = np.array([])  # empty chamber volume
        self.optimal_expansion_ratio = np.array([])  # optimal expansion ratio
        self.m_prop = np.array([])  # propellant mass
        self.P_0 = np.array([])  # chamber stagnation pressure
        self.P_exit = np.array([])  # exit pressure


class SRMOperation(MotorOperation):
    """
    Operation for a Solid Rocket Motor.
    """

    def __init__(self) -> None:
        """
        Initial parameters for a SRM operation.
        """
        super().__init__()

        # Grain and propellant parameters:
        self.burn_area = np.array([])
        self.propellant_volume = np.array([])
        self.web = np.array([])  # instant web thickness
        self.burn_rate = np.array([])  # burn rate

        # Correction factors:
        self.n_kin = np.array([])  # kinetics correction factor
        self.n_bl = np.array([])  # boundary layer correction factor
        self.n_tp = np.array([])  # two-phase flow correction factor
        self.n_cf = np.array([])  # thrust coefficient correction factor

        # Thrust coefficients:
        self.C_f = np.array([])  # thrust coefficient
        self.C_f_ideal = np.array([])  # ideal thrust coefficient
        self.thrust = np.array([])  # thrust force (N)
