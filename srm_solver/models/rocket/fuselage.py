# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from dataclasses import dataclass, field

from utils.geometric import get_circle_area


class DragCoefficientTypeError(Exception):
    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


@dataclass
class Fuselage:
    """
    Deals primarily with aerodynamic parameters.
    """

    length: float | int
    drag_coefficient: list[list[float, float]] | float | int
    outer_diameter: float | int
    frontal_area: float | None = field(default=None)

    def __post_init__(self):
        if self.frontal_area is None:
            self.frontal_area = self.get_diameter_frontal_area()

    def get_diameter_frontal_area(self) -> float:
        return get_circle_area(self.outer_diameter)

    def get_drag_coefficient(self, velocity: float = None):
        if isinstance(self.drag_coefficient, list[list[float, float]]):
            pass  # implement drag coefficient in function of velocity
        elif isinstance(self.drag_coefficient, float | int):
            return self.drag_coefficient
        else:
            raise DragCoefficientTypeError(
                self.drag_coefficient,
                "Type not recognized in 'drag_coefficient'",
            )
