# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from rocketsolver.models.materials import Material


class FuselageComponent(ABC):
    def __init__(
        self,
        material: Material,
        center_of_gravity: float,
        mass: float,
    ) -> None:
        self.material = material
        self.center_of_gravity = center_of_gravity
        self.mass = mass

    @abstractmethod
    def get_drag_coefficient(self) -> float:
        pass

    @abstractmethod
    def get_lift_coefficient(self) -> float:
        pass
