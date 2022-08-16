# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

from .chamber import CombustionChamber
from .nozzle import Nozzle


class MotorStructure:
    def __init__(
        self,
        safety_factor,
        dry_mass,
        nozzle: Nozzle,
        chamber: CombustionChamber,
    ):
        self.safety_factor = safety_factor
        self.dry_mass = dry_mass
        self.nozzle = nozzle
        self.chamber = chamber
