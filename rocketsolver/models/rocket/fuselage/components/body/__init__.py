# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.models.materials import Material
from rocketsolver.models.rocket.fuselage.components import FuselageComponent


class CylindricalBody(FuselageComponent):
    def __init__(
        self,
        material: Material,
        length: float,
        outer_diameter: float,
        rugosity: float,
        constant_K: float,
    ) -> None:
        super().__init__(material)

        self.length = length
        self.outer_diameter = outer_diameter
        self.rugosity = rugosity
        self.constant_K = constant_K

    @property
    def frontal_area(self) -> float:
        return np.pi * self.outer_diameter**2 / 4

    @property
    def outer_surface_area(self) -> float:
        return self.length * np.pi * (self.outer_diameter)

    def get_drag_coefficient(self) -> float:
        pass

    def get_lift_coefficient(self) -> float:
        return self.constant_K * self.outer_surface_area / self.frontal_area
