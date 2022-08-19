# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Parachutes are implemented using Strategy design pattern. The Parachute base 
class can be implemented in different ways by inheriting from it and then 
changing its methods depending on the particular parachute geometry. 
"""

from abc import ABC, abstractproperty

from rocketsolver.utils.geometric import get_circle_area


class Parachute(ABC):
    def __init__(self) -> None:
        pass

    @abstractproperty
    def drag_coefficient(self):
        pass

    @abstractproperty
    def area(self):
        pass


class HemisphericalParachute(Parachute):
    def __init__(self, diameter) -> None:
        super().__init__()
        self.diameter = diameter

    @property
    def drag_coefficient(self) -> float:
        return 0.71

    @property
    def area(self) -> float:
        return get_circle_area(self.diameter)
