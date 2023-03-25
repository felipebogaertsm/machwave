# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at me@felipebm.com.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass

import scipy.constants

from . import Propellant


class BurnRateOutOfBoundsError(Exception):
    def __init__(self, value: float) -> None:
        self.value = value
        self.message = (
            f"Chamber pressure out of bounds: {value * 1e-6:.2f} MPa"
        )

        super().__init__(self.message)


@dataclass
class SolidPropellant(Propellant):
    """
    Class that stores solid propellant data. Most of this data can be
    obtained from ProPEP3 or similar software. Burn rate data is generally
    empirical, as well as combustion efficiency.

    :param float burn_rate: Burn rate information list.
        Since the burn rate coefficients can vary with the chamber
        pressure itself, there is a particular data structure for how to
        describe this behavior.
        Example:
            [{'min': 0, 'max': 1e6, 'a': 8.875, 'n': 0.619}]
        Where:
            min = Minimum chamber pressure [Pa]
            max = Maximum chamber pressure [Pa]
            a = Burn rate coefficient [kg/s/Pa^n]
            n = Burn rate exponent
        The example above tells that the burn rate coefficients - a and n
        - are 8.875 and 0.619, respectively, within the range of 0 to 1
        MPa.
        The list must be ordered by increasing min value.
    :param float combustion_efficiency: Combustion, two phase,
        heat loss, friction efficiency (0 to 1)
    :param float density: Propellant density [kg/m^3]
    :param float k_mix_ch: Isentropic exponent (chamber)
    :param float k_2ph_ex: Isentropic exponent (exhaust)
    :param float T0_ideal: Ideal combustion temperature [K]
    :param float M_ch: Molar weight (chamber) [100g/mole]
    :param float M_ex: Molar weight (exhaust) [100g/mole]
    :param float Isp_frozen: Frozen specific impulse [s]
    :param float Isp_shifting: Shipping specific impulse [s]
    :param float qsi_ch: Number of condensed phase moles per 100 gram
        (chamber) [moles]
    :param float qsi_ex: Number of condensed phase moles per 100 gram
        (exhaust) [moles]
    """

    burn_rate: list[dict[str, float | int]]
    combustion_efficiency: float
    density: float
    k_mix_ch: float
    k_2ph_ex: float
    T0_ideal: float
    M_ch: float
    M_ex: float
    Isp_frozen: float
    Isp_shifting: float
    qsi_ch: float
    qsi_ex: float

    def __post_init__(self) -> None:
        # Real combustion temperature based on the ideal temperature and the
        # combustion efficiency [K]:
        self.T0 = self.T0_ideal * self.combustion_efficiency

        # Gas constant per molecular weight calculations:
        self.R_ch = scipy.constants.R / self.M_ch
        self.R_ex = scipy.constants.R / self.M_ex

    def get_burn_rate(self, chamber_pressure: float) -> float:
        """
        :param float chamber_pressure: Instantaneous stagnation pressure [Pa]
        :return: Instantaneous burn rate using St. Robert's law
        :rtype: float
        :raises BurnRateOutOfBoundsError: If the chamber pressure is out of
            the burn rate range.
        """
        for item in self.burn_rate:
            if item["min"] <= chamber_pressure <= item["max"]:
                a = item["a"]
                n = item["n"]
                return (a * (chamber_pressure * 1e-6) ** n) * 1e-3  # in m/s

        raise BurnRateOutOfBoundsError(chamber_pressure)
