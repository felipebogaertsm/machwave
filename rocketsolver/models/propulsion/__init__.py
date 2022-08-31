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

import pandas as pd
import numpy as np

from rocketsolver.models.propulsion.grain import Grain
from rocketsolver.models.propulsion.propellant import Propellant
from rocketsolver.models.propulsion.structure import MotorStructure, Nozzle
from rocketsolver.utils.isentropic_flow import (
    get_thrust_coefficients,
    get_thrust_from_cf,
    get_thrust_coefficient,
    get_total_impulse,
    get_specific_impulse,
)
from rocketsolver.utils.units import convert_mpa_to_pa
from rocketsolver.utils.utilities import generate_eng


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
    def get_launch_mass(self) -> float:
        """
        Calculates the total mass of the rocket before launch.

        :return: Total mass of the rocket before launch, in kg
        :rtype: float
        """
        pass

    @abstractmethod
    def get_dry_mass(self) -> float:
        """
        Calculates the dry mass of the rocket at any time.

        :return: Dry mass of the rocket, in kg
        :rtype: float
        """
        pass

    @abstractmethod
    def get_center_of_gravity(self) -> np.ndarray:
        """
        Calculates center of gravity of the propulsion system.

        Coordinate system is originated in the point defined by the nozzle's
        exit area surface and the combustion chamber axis.

        :return: Center of gravity position, in m, [x, y, z]
        :rtype: np.ndarray
        """
        pass

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

    def get_launch_mass(self) -> float:
        return self.structure.dry_mass + self.initial_propellant_mass

    def get_dry_mass(self) -> float:
        return self.structure.dry_mass

    def get_center_of_gravity(self) -> np.ndarray:
        """
        Constant CG throughout the operation. Half the chamber length.
        """
        return np.array([self.structure.chamber.length / 2, 0, 0])


class MotorFromDataframe(Motor):
    def __init__(
        self,
        dataframe: pd.DataFrame,
        nozzle: Nozzle,
        propellant: Propellant,
        initial_propellant_mass: float,
        dry_mass: float,
        length: float,
    ) -> None:
        self.dataframe = dataframe
        self.nozzle = nozzle
        self.propellant = propellant
        self.initial_propellant_mass = initial_propellant_mass
        self.dry_mass = dry_mass
        self.length = length

    def get_from_df(self, column_name: str) -> np.ndarray:
        return self.dataframe[column_name].to_numpy()

    def get_launch_mass(self) -> float:
        return self.initial_propellant_mass + self.dry_mass

    def get_dry_mass(self) -> float:
        return self.dry_mass

    def get_thrust(self) -> np.ndarray:
        return self.get_from_df(self.thrust_header_name)

    def get_time(self) -> np.ndarray:
        return self.get_from_df(self.time_header_name)

    def get_pressure(self) -> np.ndarray:
        return convert_mpa_to_pa(self.get_from_df(self.pressure_header_name))

    def get_thrust_coefficient(self) -> np.ndarray:
        return get_thrust_coefficient(
            P_0=self.get_pressure(),
            thrust=self.get_thrust(),
            nozzle_throat_area=self.nozzle.get_throat_area(),
        )

    def generate_eng_file(self, name: str, manufacturer: str) -> None:
        generate_eng(
            time=self.get_time(),
            thrust=self.get_thrust(),
            propellant_mass=self.get_propellant_mass(),
            name=name,
            manufacturer=manufacturer,
            chamber_length=1670,
            outer_diameter=141.3,
            motor_mass=17,
        )

    @property
    def thrust_time(self) -> float:
        return self.get_time()[-1] - self.get_time()[0]

    @property
    def thrust_time(self) -> float:
        return self.get_time()[-1] - self.get_time()[0]

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

    def get_center_of_gravity(self) -> np.ndarray:
        return np.array([self.length / 2, 0, 0])
