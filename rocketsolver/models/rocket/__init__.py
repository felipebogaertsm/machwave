# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from rocketsolver.models.fuselage import Fuselage, Fuselage3D
from rocketsolver.models.propulsion import Motor
from rocketsolver.models.recovery import Recovery


class RocketBaseClass(ABC):
    """
    Base class for a Rocket.
    """

    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage | Fuselage3D,
    ) -> None:
        self.propulsion = propulsion
        self.recovery = recovery
        self.fuselage = fuselage

    @abstractmethod
    def get_launch_mass(self) -> float:
        pass

    @abstractmethod
    def get_dry_mass(self) -> float:
        pass


class Rocket(RocketBaseClass):
    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage,
        mass_without_motor: float,
    ) -> None:
        super().__init__(
            propulsion=propulsion,
            recovery=recovery,
            fuselage=fuselage,
        )

        self.mass_without_motor = mass_without_motor

    def get_launch_mass(self) -> float:
        return self.mass_without_motor + self.propulsion.get_launch_mass()

    def get_dry_mass(self) -> float:
        return self.mass_without_motor + self.propulsion.get_dry_mass()


class Rocket3D(RocketBaseClass):
    def __init__(
        self,
        propulsion: Motor,
        recovery: Recovery,
        fuselage: Fuselage3D,
        center_of_pressure: float,
    ) -> None:
        super().__init__(
            propulsion=propulsion, recovery=recovery, fuselage=fuselage
        )

        self._center_of_pressure = center_of_pressure

    def get_center_of_pressure(self) -> float:
        """
        Returns the center of pressure position, from the nose of the rocket.

        :return: Center of pressure position, in meters.
        :rtype: float
        """
        return self._center_of_pressure

    def get_launch_mass(self) -> float:
        return self.propulsion.get_launch_mass() + self.fuselage.get_mass()

    def get_dry_mass(self) -> float:
        return self.propulsion.get_dry_mass() + self.fuselage.get_mass()
