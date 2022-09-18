# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from typing import Optional

import numpy as np

from ..fins import Fins
from rocketsolver.models.materials import Material
from rocketsolver.models.fuselage.components import FuselageComponent


class BodySegment(FuselageComponent):
    pass


class CylindricalBody(BodySegment):
    def __init__(
        self,
        material: Material,
        center_of_gravity: float,
        mass: float,
        length: float,
        outer_diameter: float,
        rugosity: float,
        constant_K: float,
        fins: Optional[Fins] = None,
    ) -> None:
        self.length = length
        self.outer_diameter = outer_diameter
        self.rugosity = rugosity
        self.constant_K = constant_K
        self.fins = fins

        super().__init__(
            material=material, center_of_gravity=center_of_gravity, mass=mass
        )

    @property
    def frontal_area(self) -> float:
        return np.pi * self.outer_diameter**2 / 4

    @property
    def outer_surface_area(self) -> float:
        return self.length * np.pi * (self.outer_diameter)

    @property
    def is_valid(self) -> None:
        assert self.rugosity < 1e-3
        assert self.frontal_area > 0
        assert self.outer_surface_area > 0

    def get_cd_body(
        self, total_vehicle_length: float, nose_cone_length: float
    ) -> float:
        """
        Not tested.
        """
        return (
            1
            + 60 / ((total_vehicle_length / self.outer_diameter) ** 3)
            + 0.0025
            * (self.length / self.outer_diameter)
            * (
                2.7 * (nose_cone_length / self.outer_diameter)
                + 4 * (self.length / self.outer_diameter)
            )
        )

    def get_cd_base(self) -> float:
        """
        Not tested.
        """
        return 0.029 / np.sqrt(
            self.get_cd_body(total_vehicle_length=0, nose_cone_length=0)
        )

    def get_drag_coefficient(
        self,
        total_vehicle_length: float,
        nose_cone_length: float,
    ) -> float:
        """
        Not tested.
        """
        return (
            self.get_cd_body(
                total_vehicle_length=total_vehicle_length,
                nose_cone_length=nose_cone_length,
            )
            + self.get_cd_base()
        )

    def get_lift_coefficient(self) -> float:
        """
        Not tested.
        """
        return self.constant_K * self.outer_surface_area / self.frontal_area
