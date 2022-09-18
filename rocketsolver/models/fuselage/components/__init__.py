# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

from rocketsolver.models.materials import Material


class FuselageComponentError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


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

        self.is_valid

    @abstractmethod
    def get_drag_coefficient(self, *args, **kwargs) -> float:
        pass

    @abstractmethod
    def get_lift_coefficient(self, *args, **kwargs) -> float:
        pass

    @property
    @abstractmethod
    def is_valid(self) -> None:
        pass
