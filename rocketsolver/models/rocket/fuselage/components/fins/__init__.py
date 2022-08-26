# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

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
