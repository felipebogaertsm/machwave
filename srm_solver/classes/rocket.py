# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Rocket class and methods.
"""


class Rocket:
    def __init__(self, mass_wo_motor, drag_coeff, rocket_outer_diameter):
        self.mass_wo_motor = mass_wo_motor
        self.drag_coeff = drag_coeff
        self.rocket_outer_diameter = rocket_outer_diameter
