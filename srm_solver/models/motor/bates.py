# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores BATES class and methods.
"""

import numpy as np

from utils.geometric import get_circle_area


class Bates:
    def __init__(
        self,
        segment_count: int,
        segment_spacing: float,
        outer_diameter: float,
        core_diameter: np.array,
        segment_length: np.array,
    ) -> None:
        self.segment_count = segment_count
        self.segment_spacing = segment_spacing
        self.outer_diameter = outer_diameter
        self.core_diameter = core_diameter
        self.segment_length = segment_length

    @property
    def total_length(self) -> float:
        return (
            np.sum(self.segment_length)
            + (self.segment_count - 1) * self.segment_spacing
        )

    def get_optimal_segment_length(self) -> np.array:
        """
        Returns the optimal length for each of the input grains.
        """
        optimal_grain_length = (
            1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)
        )
        return optimal_grain_length

    def get_mass_flux_per_segment(
        self,
        burn_rate: np.array,
        propellant_density: np.array,
        web_thickness: np.array,
    ) -> np.array:
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
        """
        segment_mass_flux = np.zeros(
            (self.segment_count, np.size(web_thickness))
        )
        segment_mass_flux = np.zeros(
            (self.segment_count, np.size(web_thickness))
        )
        total_grain_Ab = np.zeros((self.segment_count, np.size(web_thickness)))

        for j in range(self.segment_count):
            for i in range(np.size(burn_rate)):
                for k in range(j + 1):
                    total_grain_Ab[j, i] = total_grain_Ab[
                        j, i
                    ] + self.get_burn_area_per_segment(k, web_thickness[i])
                segment_mass_flux[j, i] = (
                    total_grain_Ab[j, i] * propellant_density * burn_rate[i]
                )
                segment_mass_flux[j, i] = segment_mass_flux[j, i] / (
                    get_circle_area(self.core_diameter[j] + web_thickness[i])
                )

        return segment_mass_flux

    def get_burn_area_per_segment(
        self, segment_index: int, web_thickness: float
    ) -> float:
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.segment_length

        if 0.5 * (D_grain - D_core[segment_index]) >= web_thickness:
            return np.pi * (
                (
                    (D_grain ** 2)
                    - (D_core[segment_index] + 2 * web_thickness) ** 2
                )
                / 2
                + (
                    (L_grain[segment_index] - 2 * web_thickness)
                    * (D_core[segment_index] + 2 * web_thickness)
                )
            )
        else:
            return 0

    def get_burn_area(self, web_thickness: float) -> float:
        """
        Calculates the BATES burn area given the web distance.
        """
        return np.sum(
            np.array(
                [
                    self.get_burn_area_per_segment(i, web_thickness)
                    for i in range(self.segment_count)
                ]
            )
        )

    def get_propellant_volume_per_segment(
        self,
        segment_index: int,
        web_thickness: float,
    ) -> float:
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.segment_length

        if 0.5 * (D_grain - D_core[segment_index]) >= web_thickness:
            return (np.pi / 4) * (
                (
                    (D_grain ** 2)
                    - ((D_core[segment_index] + 2 * web_thickness) ** 2)
                )
                * (L_grain[segment_index] - 2 * web_thickness)
            )
        else:
            return 0

    def get_propellant_volume(self, web_thickness: float) -> float:
        """
        Calculates the BATES grain volume given the web distance.
        """
        return np.sum(
            np.array(
                [
                    self.get_propellant_volume_per_segment(i, web_thickness)
                    for i in range(self.segment_count)
                ]
            )
        )

    def get_burn_profile(self, burn_area: np.array) -> str:
        """
        Returns string with burn profile.
        """
        if burn_area[0] / burn_area[-1] > 1.02:
            return "regressive"
        elif burn_area[0] / burn_area[-1] < 0.98:
            return "progressive"
        else:
            return "neutral"
