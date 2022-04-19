# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.


from utils.geometric import get_circle_area


class Fuselage:
    def __init__(
        self,
        length: float,
        drag_coefficient: float,
        outer_diameter: float,
        frontal_area: float = None,
    ) -> None:
        self.length = length
        self.drag_coefficient = drag_coefficient
        self.outer_diameter = outer_diameter
        self.frontal_area = frontal_area

    def get_frontal_area(self):
        if self.frontal_area is not None:
            return self.frontal_area
        else:
            return get_circle_area(self.outer_diameter)
