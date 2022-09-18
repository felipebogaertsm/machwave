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


class Fuselage3DValidationError(Exception):
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
        inertia_tensor: np.ndarray,
    ) -> None:
        self.nose_cone = nose_cone
        self.mass_without_motor = mass_without_motor
        self.inertia_tensor = np.array(inertia_tensor)

        self.body_segments: list[BodySegment] = []

    @property
    def moment_of_intertia_tensor(self):
        return self.inertia_tensor

    def get_drag_coefficient(self, velocity: float, mach_no: float) -> float:
        """
        Not tested.
        """
        return self.nose_cone.get_drag_coefficient(velocity, mach_no) + np.sum(
            [
                body_segment.get_drag_coefficient(velocity, mach_no)
                for body_segment in self.body_segments
            ]
        )

    def get_lift_coefficient(self, velocity: float, mach_no: float) -> float:
        """
        Not tested.
        """
        return self.nose_cone.get_lift_coefficient(velocity, mach_no) + np.sum(
            [
                body_segment.get_lift_coefficient(velocity, mach_no)
                for body_segment in self.body_segments
            ]
        )

    def add_body_segment(self, body_segment: BodySegment) -> None:
        self.body_segments.append(body_segment)

    @property
    def is_valid(self) -> None:
        self.nose_cone.is_valid

    def get_mass(self):
        return self.mass_without_motor
