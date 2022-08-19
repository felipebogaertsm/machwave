# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores MotorStructure class and methods.
"""

import numpy as np

from .chamber import CombustionChamber
from rocketsolver.utils.geometric import get_circle_area
from rocketsolver.utils.isentropic_flow import get_divergent_correction_factor


class Nozzle:
    def __init__(
        self,
        throat_diameter,
        divergent_angle,
        convergent_angle,
        expansion_ratio,
        material=None,
    ) -> None:
        self.throat_diameter = throat_diameter
        self.divergent_angle = divergent_angle
        self.convergent_angle = convergent_angle
        self.expansion_ratio = expansion_ratio
        self.material = material

    def get_throat_area(self):
        return get_circle_area(self.throat_diameter)

    def get_divergent_correction_factor(self):
        return get_divergent_correction_factor(self.divergent_angle)

    def get_nozzle_wall_thickness(
        self,
        chamber_pressure: float,
        safety_factor: float,
        chamber_inner_diameter: float,
        wall_angle: float,
    ) -> float:
        """
        Considers thin wall approximation.
        """
        return (chamber_pressure * chamber_inner_diameter / 2) / (
            (
                self.material.yield_strength / safety_factor
                - 0.6 * chamber_pressure * (np.cos(np.deg2rad(wall_angle)))
            )
        )

    def get_nozzle_thickness(
        self,
        chamber_pressure: np.ndarray,
        safety_factor: float,
        chamber: CombustionChamber,
    ):
        """
        Returns nozzle convergent and divergent thickness.
        """
        nozzle_conv_thickness = self.get_nozzle_wall_thickness(
            chamber_pressure,
            safety_factor,
            chamber.inner_diameter,
            self.convergent_angle,
        )

        nozzle_div_thickness = self.get_nozzle_wall_thickness(
            chamber_pressure,
            safety_factor,
            chamber.inner_diameter,
            self.divergent_angle,
        )

        return nozzle_conv_thickness, nozzle_div_thickness
