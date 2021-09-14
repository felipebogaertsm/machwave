# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores BATES class and methods.
"""


class BATES:
    def __init__(self,
        segment_count: int,
        outer_diameter: float,
        core_diameter: np.array,
        segment_length: np.array,
    ):
        self.segment_count = segment_count
        self.outer_diameter = outer_diameter
        self.core_diameter = core_diameter
        self.segment_length = segment_length

    def get_optimal_segment_length(self):
        """ Returns the optimal length for each of the input grains. """
        optimal_grain_length = 1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)
        return optimal_grain_length

    def get_mass_flux_per_segment(self, grain, r: float, pp, x):
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
         """
        segment_mass_flux = np.zeros((self.segment_count, np.size(x)))
        segment_mass_flux = np.zeros((self.segment_count, np.size(x)))
        total_grain_Ab = np.zeros((self.segment_count, np.size(x)))
        for j in range(self.segment_count):
            for i in range(np.size(r)):
                for k in range(j + 1):
                    total_grain_Ab[j, i] = total_grain_Ab[j, i] + get_burn_area(grain, x[i], k)
                segment_mass_flux[j, i] = (total_grain_Ab[j, i] * pp * r[i])
                segment_mass_flux[j, i] = (segment_mass_flux[j, i]) / get_circle_area(self.core_diameter[j] + x[i])
        return segment_mass_flux
