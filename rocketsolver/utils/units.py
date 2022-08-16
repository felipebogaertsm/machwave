# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Unit conversion functions.
"""


def convert_pa_to_psi(pressure_pa):
    """
    Converts Pascal pressure to PSI.
    """
    return pressure_pa * 1.45e-4


def convert_pa_to_mpa(pressure_pa):
    """
    Converts Pascal pressure to MPa.
    """
    return pressure_pa * 1e-6


def convert_mpa_to_pa(pressure_mpa):
    """
    Converts MPa pressure to Pascal.
    """
    return pressure_mpa / 1e-6


def convert_mass_flux_metric_to_imperial(mass_flux_metric):
    """
    Converts a mass flux in kg/s-m-m to lb/s-in-in.
    """
    return mass_flux_metric * 1.42233e-3


def convert_burn_rate_coefficient_to_metric(
    a_imperial: float, n: float
) -> float:
    return a_imperial * 25.4 / (0.0069 ** n)
