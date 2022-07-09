# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass

import numpy as np
import scipy

from . import TestData
from utils.isentropic_flow import get_total_impulse, get_specific_impulse


@dataclass
class SRMTestData(TestData):
    initial_propellant_mass: float

    def get_thrust(self, col_name="Force (N)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_time(self, col_name="Time (s)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_pressure(self, col_name="Pressure (Pa)") -> np.ndarray:
        return self.get_from_df(col_name)

    def get_temperatures(
        self, col_name_startswith="Temperature"
    ) -> np.ndarray:
        """
        :param str col_name_startswith: The name that the column starts with
        :return: An array of temperatures captured by each thermopar.
        :rtype: np.ndarray
        """
        col_names = self.data.columns.values().tolist()
        temperature_col_names = [
            col_name
            for col_name in col_names
            if col_name.startswith(col_name_startswith)
        ]

        temperatures = np.array([])

        for name in temperature_col_names:
            temperatures = np.append(temperatures, self.get_from_df(name))

        return temperatures

    def get_total_impulse(self) -> float:
        return get_total_impulse(
            np.average(self.get_thrust()), self.get_time()[-1]
        )

    def get_specific_impulse(self) -> float:
        return get_specific_impulse(
            self.get_total_impulse(), self.initial_propellant_mass
        )

    def get_instantaneous_propellant_mass(self, t: float) -> float:
        """
        IMPORTANT NOTE: this method is only an estimation of the propellant
        mass during the operation of the motor. It assumes a constant nozzle
        efficiency throughout the operation and perfect correlation between
        thrust and pressure data.

        :param float t: The time at which the propellant mass is desired
        :return: The propellant mass at time t
        :rtype: np.ndarray
        """
        t_index = np.where(self.get_time() == t)[0][0]

        time = self.get_time()[t_index:-1]
        thrust = self.get_thrust()[t_index:-1]

        return (
            np.trapz(y=thrust, x=time) / self.get_total_impulse()
        ) * self.initial_propellant_mass

    def get_propellant_mass(self) -> np.ndarray:
        """
        Calculates propellant mass for each instant and appends in an array.

        :return: The propellant mass at each time step
        :rtype: np.ndarray
        """
        return np.array(
            list(
                map(
                    lambda time: self.get_instantaneous_propellant_mass(time),
                    self.get_time(),
                )
            )
        )
