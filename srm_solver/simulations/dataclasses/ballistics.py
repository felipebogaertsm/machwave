# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Ballistics class and methods.
"""

from dataclasses import dataclass

import numpy as np


@dataclass()
class Ballistics:
    t: np.array
    y: np.array
    v: np.array
    acc: np.array
    v_rail: float
    y_burnout: float
    Mach: np.array
    apogee_time: float
    flight_time: float
    P_ext: np.array
