# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

import numpy as np

from . import BallisticOperation


class Ballistic6DOFOperation(BallisticOperation):
    @property
    def apogee(self) -> float:
        pass

    @property
    def apogee_time(self) -> float:
        pass

    @property
    def max_velocity(self) -> float:
        pass

    @property
    def max_velocity_time(self) -> float:
        pass

    @property
    def apogee_time(self) -> float:
        pass
