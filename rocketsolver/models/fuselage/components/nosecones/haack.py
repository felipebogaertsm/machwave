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
    Reference:
    THE DESCRIPTIVE GEOMETRY OF NOSE CONES, Gary Crowell, 1996
    http://servidor.demec.ufpr.br/CFD/bibliografia/aerodinamica/Crowell_1996.pdf
    Accessed September 17, 2022 at 2:01 pm EST.
    """

    def __init__(
        self,
        material: Material,
        center_of_gravity: float,
        mass: float,
        length: float,
        base_diameter: float,
        C: float,
    ) -> None:
        self.C = C

        super().__init__(
            material=material,
            center_of_gravity=center_of_gravity,
            mass=mass,
            length=length,
            base_diameter=base_diameter,
            surface_area=None,
        )

    def get_theta(self, x: float) -> float:
        """
        Theta is used to calculate the Von Karman profile along the main nose
        cone axis.
        """
        return np.arccos(1 - 2 * x / self.length)

    def get_y_from_x(self, x: float) -> float:
        """
        Calculates the y coordinate of the Von Karman profile along the x
        axis.
        """
        theta = self.get_theta(x)

        return (
            self.base_diameter
            / np.sqrt(np.pi)
            * np.sqrt(
                theta - np.sin(2 * theta) / 2 + self.C * (np.sin(theta) ** 3)
            )
        )

    @property
    def is_valid(self) -> None:
        assert self.C <= 4 / 3

    @property
    def surface_area(self) -> float:
        """
        Calculates the surface area of the Haack Series nose cone.
        """
        iterations = 1000
        area = 0  # initial value, to be incremented

        for x in np.linspace(0, self.length, iterations):
            y = self.get_y_from_x(x)
            area += 2 * np.pi * y * self.length / iterations

        return area

    def get_drag_coefficient(self, *args, **kwargs) -> float:
        return 0

    def get_lift_coefficient(self, *args, **kwargs) -> float:
        return 2
