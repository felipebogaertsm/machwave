# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from fluids.atmosphere import ATMOSPHERE_1976


class Atmosphere(ABC):
    """
    Abstract class that represents an atmospheric model.
    """

    @abstractmethod
    def get_density(self, y_amsl: float) -> float:
        pass

    @abstractmethod
    def get_gravity(self, y_amsl: float) -> float:
        pass

    @abstractmethod
    def get_pressure(self, y_amsl: float) -> float:
        pass

    @abstractmethod
    def get_sonic_velocity(self, y_amsl: float) -> float:
        pass


class Atmosphere1976(Atmosphere):
    def get_density(self, y_amsl: float) -> float:
        """
        Gets the air density using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976(y_amsl).rho

    def get_gravity(self, y_amsl: float) -> float:
        """
        Gets the gravity using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976.gravity(y_amsl)

    def get_pressure(self, y_amsl: float) -> float:
        """
        Gets the air pressure using the AMSL elevation and the fluids library.
        """
        return ATMOSPHERE_1976(y_amsl).P

    def get_sonic_velocity(self, y_amsl: float) -> float:
        return ATMOSPHERE_1976(y_amsl).v_sonic
