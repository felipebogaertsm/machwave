# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from . import GrainSegment


class BatesSegment(GrainSegment):
    def __init__(
        self,
        outer_diameter: float,
        core_diameter: float,
        length: float,
        spacing: float,
    ) -> None:
        self.outer_diameter = outer_diameter
        self.core_diameter = core_diameter
        self.length = length
        self.spacing = spacing

        self.validate_inputs()

    def validate_inputs(self) -> float:
        assert self.outer_diameter > self.core_diameter
        assert self.core_diameter > 0
        assert self.length > 0
        assert self.spacing >= 0

    @property
    def total_web_thickness(self) -> float:
        return 0.5 * (self.outer_diameter - self.core_diameter)

    def get_optimal_length(self) -> float:
        """
        Returns the optimal length for BATES segment.
        """
        optimal_grain_length = (
            1e3 * 0.5 * (3 * self.outer_diameter + self.core_diameter)
        )
        return optimal_grain_length

    def get_burn_area(self, web_thickness: float) -> float:
        # Variables with same notation as in Nakka's website
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.length

        if self.total_web_thickness >= web_thickness:
            return np.pi * (
                ((D_grain**2) - (D_core + 2 * web_thickness) ** 2) / 2
                + (
                    (L_grain - 2 * web_thickness)
                    * (D_core + 2 * web_thickness)
                )
            )
        else:
            return 0

    def get_volume(self, web_thickness: float) -> float:
        # Variables with same notation as in Nakka's website
        D_grain = self.outer_diameter
        D_core = self.core_diameter
        L_grain = self.length

        if self.total_web_thickness >= web_thickness:
            return (np.pi / 4) * (
                ((D_grain**2) - ((D_core + 2 * web_thickness) ** 2))
                * (L_grain - 2 * web_thickness)
            )
        else:
            return 0
