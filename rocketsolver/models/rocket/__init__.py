# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Rocket class and methods.
"""

import numpy as np

from .fuselage import Fuselage, Fuselage3D
from .structure import RocketStructure


class Rocket:
    def __init__(self, fuselage: Fuselage, structure: RocketStructure):
        self.fuselage = fuselage
        self.structure = structure


class Rocket3D(Rocket):
    def __init__(
        self,
        fuselage: Fuselage3D,
        structure: RocketStructure,
    ):
        """
        :param Fuselage3D fuselage: Fuselage3D object.
        :param RocketStructure structure: RocketStructure object.
        """
        super().__init__(fuselage, structure)
