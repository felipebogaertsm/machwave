# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from rocketsolver.models.materials import Material
from rocketsolver.models.fuselage.components import FuselageComponent


class Fins(FuselageComponent):
    def __init__(
        self,
        material: Material,
        center_of_gravity: float,
        mass: float,
        thickness: float,
        count: int,
        rugosity: float,
    ) -> None:
        super().__init__(
            material=material, center_of_gravity=center_of_gravity, mass=mass
        )

        self.thickness = thickness
        self.count = count
        self.rugosity = rugosity
