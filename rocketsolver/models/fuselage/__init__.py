# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from .components.body import BodySegment
from .components.nosecones import NoseCone
from rocketsolver.utils.geometric import get_circle_area


class DragCoefficientTypeError(Exception):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class Fuselage:
    """
    Deals primarily with aerodynamic parameters.
    """

    def __init__(
        self,
        length: float,
        outer_diameter: float,
        drag_coefficient: list[list[float, float]] | float | int,
        frontal_area: float | None = None,
    ) -> None:
        self.length = length
        self.outer_diameter = outer_diameter
        self._drag_coefficient = drag_coefficient
        self._frontal_area = frontal_area or get_circle_area(outer_diameter)

    @property
    def frontal_area(self) -> float:
        if self._frontal_area is None:
            return get_circle_area(self.outer_diameter)
        else:
            return self._frontal_area

    def get_drag_coefficient(self, velocity: float = None) -> float:
        if isinstance(self._drag_coefficient, list):
            pass  # still need to implement drag coefficient in function of velocity
        elif isinstance(self._drag_coefficient, (float, int)):
            return self._drag_coefficient
        else:
            raise DragCoefficientTypeError(
                self._drag_coefficient,
                "Type not recognized in 'drag_coefficient'",
            )


class Fuselage3D:
    def __init__(
        self,
        nose_cone: NoseCone,
        mass_without_motor: float,
        I_x: float,
        I_y: float,
        I_z: float,
        I_xy: float,
        I_xz: float,
        I_yz: float,
        I_yx: float,
        I_zx: float,
        I_zy: float,
    ) -> None:
        # Moment of inertia for each axis:
        self.I_x = I_x
        self.I_y = I_y
        self.I_z = I_z
        self.I_xy = I_xy
        self.I_xz = I_xz
        self.I_yz = I_yz
        self.I_yx = I_yx
        self.I_zx = I_zx
        self.I_zy = I_zy

        self.moment_of_inertia_matrix = [
            [I_x, -I_xy, -I_xz],
            [-I_yx, I_y, -I_yz],
            [-I_zx, -I_zy, I_z],
        ]

        self.nose_cone = nose_cone
        self.mass_without_motor = mass_without_motor
        self.body_segments: list[BodySegment] = []

    def get_drag_coefficient(
        self, velocity: float = None, mach_no: float = None
    ) -> float:
        return self.nose_cone.get_drag_coefficient() + np.sum(
            [
                body_segment.get_drag_coefficient()
                for body_segment in self.body_segments
            ]
        )

    def add_body_segment(self, body_segment: BodySegment) -> None:
        self.body_segments.append(body_segment)

    def get_mass(self):
        return self.mass_without_motor
