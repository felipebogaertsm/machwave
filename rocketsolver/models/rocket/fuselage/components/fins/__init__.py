# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from rocketsolver.models.materials import Material
from rocketsolver.models.rocket.fuselage.components import FuselageComponent
from rocketsolver.utils.geometric import get_trapezoidal_area


class TrapezoidalFins(FuselageComponent):
    def __init__(
        self,
        material: Material,
        thickness: float,
        base_length: float,
        tip_length: float,
        height: float,
    ) -> None:
        super().__init__(material)

        self.tickness = thickness
        self.base_length = base_length
        self.tip_length = tip_length
        self.height = height

    def get_area(self):
        return get_trapezoidal_area(
            self.base_length, self.tip_length, self.height
        )

    def get_AR(self):
        return ((self.base_length / 2) ** 2) / self.get_area()

    def get_A_1_4(self) -> float:
        return np.deg2rad(45)

    def get_lift_coefficient(self, *args, **kwargs) -> float:
        return (2 * np.pi * self.get_AR()) / (
            2
            + np.cos(self.get_A_1_4())
            * np.sqrt(
                4 + ((self.get_AR() ** 2) / (np.cos(self.get_A_1_4()) ** 4))
            )
        )
