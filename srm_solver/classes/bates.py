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
        N: int,
        D_grain: float,
        D_core: np.array,
        L_grain: np.array,
    ):
        self.N = N
        self.D_grain = D_grain
        self.D_core = D_core
        self.L_grain = L_grain

    def get_optimal_segment_length(self):
        """ Returns the optimal length for each of the input grains. """
        optimal_grain_length = 1e3 * 0.5 * (3 * self.D_grain + self.D_core)
        return optimal_grain_length

    def get_mass_flux_per_segment(self, grain, r: float, pp, x):
        """
        Returns a numpy multidimensional array with the mass flux for each
        grain.
         """
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        segment_mass_flux = np.zeros((self.N, np.size(x)))
        total_grain_Ab = np.zeros((self.N, np.size(x)))
        for j in range(self.N):
            for i in range(np.size(r)):
                for k in range(j + 1):
                    total_grain_Ab[j, i] = total_grain_Ab[j, i] + get_burn_area(grain, x[i], k)
                segment_mass_flux[j, i] = (total_grain_Ab[j, i] * pp * r[i])
                segment_mass_flux[j, i] = (segment_mass_flux[j, i]) / get_circle_area(self.D_core[j] + x[i])
        return segment_mass_flux
