# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from rocketsolver.models.materials import Material
from rocketsolver.models.rocket.fuselage.components import FuselageComponent


class NoseCone(FuselageComponent):
    def __init__(
        self,
        material: Material,
        length: float,
        base_diameter: float,
        surface_area: float,
    ) -> None:
        super().__init__(material)

        self.length = length
        self.base_diameter = base_diameter
        self._surface_area = surface_area

    @property
    def surface_area(self) -> float:
        return self._surface_area
