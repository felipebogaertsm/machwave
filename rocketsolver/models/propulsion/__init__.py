# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Motor class and methods.
"""

from abc import ABC, abstractmethod

from rocketsolver.models.propulsion.grain import Grain
from rocketsolver.models.propulsion.propellant import Propellant
from rocketsolver.models.propulsion.structure import MotorStructure
from rocketsolver.utils.isentropic_flow import (
    get_thrust_coefficients,
    get_thrust_from_cf,
)


class Motor(ABC):
    """
    Abstract rocket motor/engine class. Can be used to model any chemical
    rocket propulsion system, such as Solid, Hybrid and Liquid.
    """

    def __init__(
        self,
        propellant: Propellant,
        structure: MotorStructure,
    ) -> None:
        """
        Instantiates object attributes common to any motor/engine (Solid,
        Hybrid or Liquid).

        :param Propellant propellant: Object representing the propellant used in the motor
        :param MotorStructure structure: Object representing the structure of the motor
        :rtype: None
        """
        self.propellant = propellant
        self.structure = structure

    @abstractmethod
    def get_thrust_coefficient_correction_factor(self) -> float:
        """
        Calculates the thrust coefficient correction factor. This factor is
        adimensional and should be applied to the ideal thrust coefficient to
        get the real thrust coefficient.

        :return: Thrust coefficient correction factor
        :rtype: float
        """
        pass

    @abstractmethod
    def get_thrust_coefficient(self) -> float:
        """
        Calculates the thrust coefficient at a particular instant.

        :return: Thrust coefficient
        :rtype: float
        """
        pass

    def get_thrust(self, cf: float, chamber_pressure: float) -> float:
        """
        Calculates the thrust based on instantaneous thrust coefficient and
        chamber pressure.

        Utilized nozzle throat area from the structure and nozzle classes.

        :param float cf: Instantaneous thrust coefficient, adimensional
        :param float chamber_pressure: Instantaneous chamber pressure, in Pa
        :return: Instantaneous thrust, in Newtons
        :rtype: float
        """
        return get_thrust_from_cf(
            cf,
            chamber_pressure,
            self.structure.nozzle.get_throat_area(),
        )


class SolidMotor(Motor):
    def __init__(
        self,
        grain: Grain,
        propellant: Propellant,
        structure: MotorStructure,
    ) -> None:
        self.grain = grain
        super().__init__(propellant, structure)

        self.cf_ideal = None  # ideal thrust coefficient
        self.cf_real = None  # real thrust coefficient

    def get_free_chamber_volume(self, propellant_volume: float) -> float:
        """
        Calculates the chamber volume without any propellant.

        :param float propellant_volume: Propellant volume, in m^3
        :return: Free chamber volume, in m^3
        :rtype: float
        """
        return self.structure.chamber.get_empty_volume() - propellant_volume

    @property
    def initial_propellant_mass(self) -> float:
        """
        :return: Initial propellant mass, in kg
        :rtype: float
        """
        return (
            self.grain.get_propellant_volume(web_thickness=0)
            * self.propellant.density
        )

    def get_thrust_coefficient_correction_factor(
        self, n_kin: float, n_bl: float, n_tp: float
    ) -> float:
        """
        :param float n_kin: Kinematic correction factor, adimensional
        :param float n_bl: Boundary layer correction factor, adimensional
        :param float n_tp: Two-phase correction factor, adimensional
        :return: Thrust coefficient correction factor, adimensional
        :rtype: float
        """
        return (
            (100 - (n_kin + n_bl + n_tp))
            * self.structure.nozzle.get_divergent_correction_factor()
            / 100
            * self.propellant.combustion_efficiency
        )

    def get_thrust_coefficient(
        self,
        chamber_pressure: float,
        exit_pressure: float,
        external_pressure: float,
        expansion_ratio: float,
        k_2ph_ex: float,
        n_cf: float,
    ) -> float:
        """
        :param float chamber_pressure: Chamber pressure, in Pa
        :param float exit_pressure: Exit pressure, in Pa
        :param float external_pressure: External pressure, in Pa
        :param float expansion_ratio: Expansion ratio, adimensional
        :param float k_2ph_ex: Two-phase isentropic coefficient, adimensional
        :param float n_cf: Thrust coefficient correction factor, adimensional
        :return: Instanteneous thrust coefficient, adimensional
        :rtype: float
        """
        self.cf_ideal, self.cf_real = get_thrust_coefficients(
            chamber_pressure,
            exit_pressure,
            external_pressure,
            expansion_ratio,
            k_2ph_ex,
            n_cf,
        )
        return self.cf_real
