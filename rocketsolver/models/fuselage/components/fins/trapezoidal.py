# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from . import Fins
from rocketsolver.models.materials import Material
from rocketsolver.utils.geometric import get_trapezoidal_area


class TrapezoidalFins(Fins):
    def __init__(
        self,
        material: Material,
        center_of_gravity: float,
        mass: float,
        thickness: float,
        count: int,
        rugosity: float,
        base_length: float,
        tip_length: float,
        average_span: float,
        height: float,
        body_diameter: float,
    ) -> None:
        super().__init__(
            material=material,
            center_of_gravity=center_of_gravity,
            mass=mass,
            thickness=thickness,
            count=count,
            rugosity=rugosity,
        )

        self.base_length = base_length
        self.tip_length = tip_length
        self.average_span = average_span
        self.height = height
        self.body_diameter = body_diameter

    def get_area(self):
        return get_trapezoidal_area(
            self.base_length, self.tip_length, self.height
        )

    def get_K_f(self) -> float:
        return 1 + (
            (self.body_diameter / 2) / (self.height + (self.body_diameter / 2))
        )

    def get_drag_coefficient(self, *args, **kwargs) -> float:
        """
        Assuming 0 drag from fins.
        """
        return 0

    def get_lift_coefficient(self, *args, **kwargs) -> float:
        """
        Not tested.
        """
        return self.get_K_f * (
            (4 * self.count * (self.height / self.body_diameter) ** 2)
            / (
                1
                + np.sqrt(
                    1
                    + 2
                    * self.average_span
                    / (self.base_length + self.tip_length)
                )
            )
        )

    @property
    def is_valid(self) -> None:
        pass
