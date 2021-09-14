# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores the functions that solve isentropic flow equations.
"""

import numpy as np


def get_circle_area(diameter):
    """ Returns the area of the circle based on circle diameter. """
    area = np.pi * 0.25 * diameter ** 2
    return area
