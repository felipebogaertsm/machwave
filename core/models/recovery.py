# -*- coding: utf-8 -*-
# Author: Felipe Bogaerts de Mattos
# Contact me at felipe.bogaerts@engenharia.ufjf.br.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

"""
Stores Recovery class and methods.
"""


class Recovery:
    def __init__(
        self,
        drogue_time,
        drag_coeff_drogue,
        drogue_diameter,
        drag_coeff_main,
        main_diameter,
        main_chute_activation_height,
    ):
        self.drogue_time = drogue_time
        self.drag_coeff_drogue = drag_coeff_drogue
        self.drogue_diameter = drogue_diameter
        self.drag_coeff_main = drag_coeff_main
        self.main_diameter = main_diameter
        self.main_chute_activation_height = main_chute_activation_height
