# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores solvers usually called on functions that solve ODEs.
"""

import numpy as np


def solve_cp_seidel(
    P0: float,
    Pe: float,
    Ab: float,
    V0: float,
    At: float,
    pp: float,
    k: float,
    R: float,
    T0: float,
    r: float
    ):
    """
    Calculates the chamber pressure by solving Hans Seidel's differential
    equation.
    """
    P_critical_ratio = (2 / (k + 1)) ** (k / (k - 1))
    if Pe / P0 <= P_critical_ratio:
        H = ((k / (k + 1)) ** 0.5) * ((2 / (k + 1)) ** (1 / (k - 1)))
    else:
        H = ((Pe / P0) ** (1 / k)) * \
            (((k / (k - 1)) * (1 - (Pe / P0) ** ((k - 1) / k))) ** 0.5)
    dP0dt = ((R * T0 * Ab * pp * r) -
             (P0 * At * H * ((2 * R * T0) ** 0.5))) / V0
    return dP0dt
