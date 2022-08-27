# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from . import NoseCone
from rocketsolver.models.materials import Material


class HaackSeriesNoseCone(NoseCone):
    """
    https://en.wikipedia.org/wiki/Nose_cone_design#Von_K%C3%A1rm%C3%A1n
    """

    def __init__(
        self,
        material: Material,
        length: float,
        base_diameter: float,
        C: float,
    ) -> None:
        super().__init__(
            material,
            length,
            base_diameter,
            None,
        )

        self.C = C

    def get_theta(self, x: float) -> float:
        return np.arcos(1 - 2 * x / self.length)

    def get_y_from_x(self, x: float) -> float:
        theta = self.get_theta(x)

        return (
            self.base_diameter
            / np.sqrt(np.pi)
            * np.sqrt(
                theta - np.sin(2 * theta) / 2 + self.C * (np.sin(theta) ** 3)
            )
        )

    @property
    def surface_area(self) -> float:
        iterations = 1000
        area = 0  # initial value, to be incremented

        for x in np.linspace(0, self.length, iterations):
            y = self.get_y_from_x(x)
            area += 2 * np.pi * y * self.length / iterations

        return area
