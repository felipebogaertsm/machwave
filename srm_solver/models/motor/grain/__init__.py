# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from abc import ABC, abstractmethod

import numpy as np


class GrainSegment(ABC):
    @abstractmethod
    def get_burn_area(self, web_distance: float) -> float:
        pass

    @abstractmethod
    def get_propellant_volume(self, web_distance: float) -> float:
        pass

    @abstractmethod
    def get_mass_flux(self) -> np.array:
        pass


class Grain(ABC):
    def __init__(self) -> None:
        self.segments: list[GrainSegment] = []

    @abstractmethod
    def add_segment(self, new_segment: GrainSegment) -> None:
        if isinstance(new_segment, GrainSegment):
            self.segments.append(new_segment)
        else:
            raise Exception("Argument is not a GrainSegment class instance")
